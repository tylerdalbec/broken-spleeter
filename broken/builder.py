#!/usr/bin/env python
# coding: utf8

"""
Estimator spec builder that exposes the estimated masks as an interception
point.

Upstream computes masks in `EstimatorSpecBuilder._build_masks` and consumes
them immediately in `_build_masked_stfts`. This subclass splits that seam: the
computed masks stay fetchable, and a feedable tensor is spliced in between, so
a caller can read a mask, modify it, and hand it back without the graph being
rebuilt or reconstruction being reimplemented.

The splice uses `placeholder_with_default`, so leaving the mask unfed passes
the model's own estimate through untouched. Bypass is therefore structural
rather than a code path that has to be kept honest.
"""

from typing import Dict

# pyright: reportMissingImports=false
# pylint: disable=import-error
import tensorflow as tf  # type: ignore

from spleeter.model import EstimatorSpecBuilder

# pylint: enable=import-error


class InterceptingSpecBuilder(EstimatorSpecBuilder):
    """`EstimatorSpecBuilder` with a feedable mask stage."""

    def _build_masks(self) -> None:
        """
        Build the model's masks, then splice a feedable tensor in front of
        every downstream consumer.

        Populates two extra attributes:

        * `estimated_masks` — what the network produced, for fetching.
        * `mask_inputs` — what reconstruction consumes, for feeding.
        """
        super()._build_masks()
        estimated = self._masks
        inputs: Dict[str, tf.Tensor] = {}
        for instrument, mask in estimated.items():
            inputs[instrument] = tf.compat.v1.placeholder_with_default(
                mask, shape=mask.shape, name=f"mask_input/{instrument}"
            )
        self._estimated_masks = estimated
        self._mask_inputs = inputs
        self._masks = inputs

    @property
    def estimated_masks(self) -> Dict[str, tf.Tensor]:
        """The masks as computed by the network, before any interception."""
        if not hasattr(self, "_estimated_masks"):
            self._build_masks()
        return self._estimated_masks

    @property
    def mask_inputs(self) -> Dict[str, tf.Tensor]:
        """The feedable mask tensors that reconstruction consumes."""
        if not hasattr(self, "_mask_inputs"):
            self._build_masks()
        return self._mask_inputs
