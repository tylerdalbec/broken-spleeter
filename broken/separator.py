#!/usr/bin/env python
# coding: utf8

"""
Separator that owns its graph and session.

Upstream `Separator` runs inference through `tf.estimator.Estimator`, which
builds and owns its own graph and session and hands back only finished
waveforms. That is fine for ordinary separation and useless for this project,
which needs to reach the masks and the variables.

`Separator` already contains an unreachable direct-session path
(`_get_builder`, `_get_features`, `_get_session`). This module is that path
made real, and its output is bit-identical to the estimator's.
"""

import os
from os.path import basename, dirname, join, splitext
from typing import Callable, Dict, List, Optional

# pyright: reportMissingImports=false
# pylint: disable=import-error
import numpy as np
import tensorflow as tf  # type: ignore

from spleeter.audio import Codec
from spleeter.audio.adapter import AudioAdapter
from spleeter.audio.convertor import to_stereo
from spleeter.model import InputProviderFactory
from spleeter.model.provider import ModelProvider
from spleeter.types import AudioDescriptor
from spleeter.utils.configuration import load_configuration

from .builder import InterceptingSpecBuilder

# pylint: enable=import-error


MaskFunction = Callable[[Dict[str, np.ndarray]], Dict[str, np.ndarray]]


class BrokenSeparator(object):
    """Separator exposing the mask stage as an interception point."""

    def __init__(
        self, params_descriptor: str = "spleeter:2stems", MWF: bool = False
    ) -> None:
        """
        Default constructor. Nothing is built until first use; construction
        does not download checkpoints or touch TensorFlow.

        Parameters:
            params_descriptor (str):
                Descriptor for the model configuration to load.
            MWF (bool):
                (Optional) `True` if multichannel Wiener filtering should be
                used. Masks remain interceptable, but reconstruction no longer
                consumes them directly.
        """
        self._params = load_configuration(params_descriptor)
        self._params["MWF"] = MWF
        self._sample_rate = self._params["sample_rate"]
        self._graph = tf.Graph()
        self._session: Optional[tf.compat.v1.Session] = None
        self._builder: Optional[InterceptingSpecBuilder] = None
        self._input_provider = None
        self._features: Optional[Dict] = None
        self._outputs: Optional[Dict] = None

    @property
    def sample_rate(self) -> int:
        """Sample rate the loaded model expects."""
        return self._sample_rate

    @property
    def instruments(self) -> List[str]:
        """Names of the stems this model produces."""
        return list(self._params["instrument_list"])

    def _build(self) -> None:
        """
        Build the inference graph and restore the pretrained checkpoint.

        Graph construction happens inside an explicit `tf.Graph` context, which
        is what makes `tf.compat.v1.placeholder` legal without disabling eager
        execution process-wide. Several of these can coexist in one process,
        which later ensemble work will need.
        """
        model_directory = ModelProvider.default().get(self._params["model_dir"])
        self._params["model_dir"] = model_directory
        with self._graph.as_default():
            self._input_provider = InputProviderFactory.get(self._params)
            self._features = self._input_provider.get_input_dict_placeholders()
            self._builder = InterceptingSpecBuilder(self._features, self._params)
            self._outputs = {
                name: tensor
                for name, tensor in self._builder.outputs.items()
                if name != "audio_id"
            }
            saver = tf.compat.v1.train.Saver()
            session = tf.compat.v1.Session(graph=self._graph)
            saver.restore(session, tf.train.latest_checkpoint(model_directory))
            self._session = session

    def _get_session(self) -> tf.compat.v1.Session:
        """Lazy accessor for the restored session."""
        if self._session is None:
            self._build()
        return self._session

    def _check_masks(
        self,
        masks: Dict[str, np.ndarray],
        reference: Optional[Dict[str, np.ndarray]] = None,
    ) -> None:
        """
        Validate a mask dictionary before feeding it.

        Feeding a malformed mask otherwise fails inside TensorFlow with a bare
        shape error that names neither the instrument responsible nor the axis
        that went wrong.

        The frame axis is statically unknown in the graph, so it cannot be
        checked against the tensor shape. When the estimated masks are on hand
        — which is the case whenever a mask function ran — they are used as an
        exact reference instead. Otherwise only agreement between instruments
        can be enforced.

        Parameters:
            masks (Dict):
                Mask per instrument, to be fed.
            reference (Optional[Dict]):
                (Optional) Estimated masks the fed ones should match exactly.

        Raises:
            ValueError:
                If an instrument is missing or unexpected, or a mask no longer
                matches the shape reconstruction expects.
        """
        expected = self._builder.estimated_masks
        missing = set(expected) - set(masks)
        if missing:
            raise ValueError(f"masks missing instruments: {sorted(missing)}")
        unexpected = set(masks) - set(expected)
        if unexpected:
            raise ValueError(f"masks contain unknown instruments: {sorted(unexpected)}")
        for instrument, array in masks.items():
            wanted = expected[instrument].shape.as_list()
            if array.ndim != len(wanted):
                raise ValueError(
                    f"mask for {instrument} has {array.ndim} axes, "
                    f"expected {len(wanted)}"
                )
            for axis, (want, got) in enumerate(zip(wanted, array.shape)):
                if want is not None and want != got:
                    raise ValueError(
                        f"mask for {instrument} has {got} on axis {axis}, "
                        f"expected {want}"
                    )
            if reference is not None and array.shape != reference[instrument].shape:
                raise ValueError(
                    f"mask for {instrument} has shape {tuple(array.shape)}, "
                    f"expected {tuple(reference[instrument].shape)} as estimated"
                )
        frames = {array.shape[0] for array in masks.values()}
        if len(frames) > 1:
            raise ValueError(f"masks disagree on frame count: {sorted(frames)}")

    def estimate_masks(
        self, waveform: np.ndarray, audio_descriptor: AudioDescriptor = ""
    ) -> Dict[str, np.ndarray]:
        """
        Run the network and return its estimated masks without reconstructing
        audio.

        Parameters:
            waveform (np.ndarray):
                Waveform to be analyzed.
            audio_descriptor (AudioDescriptor):
                (Optional) String describing the waveform.

        Returns:
            Dict:
                Mask per instrument, shaped `(frames, bins, channels)`.
        """
        if not waveform.shape[-1] == 2:
            waveform = to_stereo(waveform)
        session = self._get_session()
        feed = self._input_provider.get_feed_dict(
            self._features, waveform, audio_descriptor
        )
        return session.run(self._builder.estimated_masks, feed_dict=feed)

    def separate(
        self,
        waveform: np.ndarray,
        audio_descriptor: AudioDescriptor = "",
        mask_fn: Optional[MaskFunction] = None,
        masks: Optional[Dict[str, np.ndarray]] = None,
    ) -> Dict[str, np.ndarray]:
        """
        Perform separation, optionally corrupting the masks on the way through.

        With neither `mask_fn` nor `masks`, the mask placeholders go unfed and
        the model's own estimates pass through, which is bit-identical to
        ordinary Spleeter.

        Parameters:
            waveform (np.ndarray):
                Waveform to be separated.
            audio_descriptor (AudioDescriptor):
                (Optional) String describing the waveform.
            mask_fn (Optional[MaskFunction]):
                (Optional) Called with the estimated masks; whatever it returns
                is fed back in their place.
            masks (Optional[Dict]):
                (Optional) Pre-computed masks to feed directly, skipping the
                network. Useful for sweeping many corruptions over one
                analysis. Mutually exclusive with `mask_fn`.

        Returns:
            Dict:
                Separated waveform per instrument.

        Raises:
            ValueError:
                If both `mask_fn` and `masks` are given.
        """
        if mask_fn is not None and masks is not None:
            raise ValueError("pass mask_fn or masks, not both")
        if not waveform.shape[-1] == 2:
            waveform = to_stereo(waveform)
        session = self._get_session()
        feed = self._input_provider.get_feed_dict(
            self._features, waveform, audio_descriptor
        )
        if mask_fn is None and masks is None:
            return session.run(self._outputs, feed_dict=feed)
        reference = None
        if mask_fn is not None:
            reference = session.run(self._builder.estimated_masks, feed_dict=feed)
            masks = mask_fn(reference)
        self._check_masks(masks, reference)
        for instrument, tensor in self._builder.mask_inputs.items():
            feed[tensor] = masks[instrument]
        try:
            return session.run(self._outputs, feed_dict=feed)
        except tf.errors.InvalidArgumentError as error:
            raise ValueError(
                "fed masks were rejected by reconstruction, most likely a frame "
                f"count that does not match this waveform: {error.message}"
            ) from error

    def load_audio(
        self,
        audio_descriptor: AudioDescriptor,
        offset: float = 0,
        duration: float = 600.0,
    ) -> np.ndarray:
        """
        Load audio at the model's sample rate.

        Parameters:
            audio_descriptor (AudioDescriptor):
                Song to load.
            offset (float):
                (Optional) Offset in seconds.
            duration (float):
                (Optional) Duration in seconds.

        Returns:
            np.ndarray:
                Loaded waveform.
        """
        waveform, _ = AudioAdapter.default().load(
            audio_descriptor,
            offset=offset,
            duration=duration,
            sample_rate=self._sample_rate,
        )
        return waveform

    def save_to_file(
        self,
        sources: Dict[str, np.ndarray],
        audio_descriptor: AudioDescriptor,
        destination: str,
        filename_format: str = "{filename}/{instrument}.{codec}",
        codec: Codec = Codec.WAV,
        bitrate: str = "128k",
    ) -> None:
        """
        Write separated sources to disk.

        Mirrors `spleeter.separator.Separator.save_to_file` minus the process
        pool, so output files are byte-comparable with the upstream CLI.

        Parameters:
            sources (Dict):
                Separated waveform per instrument.
            audio_descriptor (AudioDescriptor):
                Descriptor the sources were separated from, used for naming.
            destination (str):
                Target directory.
            filename_format (str):
                (Optional) Output filename format.
            codec (Codec):
                (Optional) Export codec.
            bitrate (str):
                (Optional) Export bitrate.
        """
        adapter = AudioAdapter.default()
        foldername = basename(dirname(audio_descriptor))
        filename = splitext(basename(audio_descriptor))[0]
        for instrument, data in sources.items():
            path = join(
                destination,
                filename_format.format(
                    filename=filename,
                    instrument=instrument,
                    foldername=foldername,
                    codec=codec,
                ),
            )
            directory = dirname(path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            adapter.save(path, data, self._sample_rate, codec, bitrate)

    def close(self) -> None:
        """Release the TensorFlow session."""
        if self._session is not None:
            self._session.close()
            self._session = None

    def __enter__(self) -> "BrokenSeparator":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
