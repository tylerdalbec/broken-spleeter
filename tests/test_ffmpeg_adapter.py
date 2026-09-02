#!/usr/bin/env python
# coding: utf8

""" Unit testing for audio adapter. """

__email__ = "spleeter@deezer.com"
__author__ = "Deezer Research"
__license__ = "MIT License"

from os.path import join
from tempfile import TemporaryDirectory

import ffmpeg  # type: ignore
import numpy as np

# pyright: reportMissingImports=false
# pylint: disable=import-error
from pytest import approx, fixture, raises

from spleeter import SpleeterError
from spleeter.audio.adapter import AudioAdapter
from spleeter.audio.ffmpeg import FFMPEGProcessAudioAdapter

# pylint: enable=import-error

TEST_AUDIO_DESCRIPTOR = "audio_example.mp3"
TEST_OFFSET = 0
TEST_DURATION = 600.0
TEST_SAMPLE_RATE = 44100
TEST_EXPECTED_SAMPLES = 479832
TEST_EXPECTED_DURATION = TEST_EXPECTED_SAMPLES / TEST_SAMPLE_RATE


@fixture(scope="session")
def adapter():
    """Target test audio adapter fixture."""
    return AudioAdapter.default()


@fixture(scope="session")
def audio_data(adapter):
    """Audio data fixture based on sample loading from adapter."""
    return adapter.load(
        TEST_AUDIO_DESCRIPTOR, TEST_OFFSET, TEST_DURATION, TEST_SAMPLE_RATE
    )


def test_default_adapter(adapter):
    """Test adapter as default adapter."""
    assert isinstance(adapter, FFMPEGProcessAudioAdapter)
    assert adapter is AudioAdapter._DEFAULT


def test_load(audio_data):
    """Test audio loading."""
    waveform, sample_rate = audio_data
    assert sample_rate == TEST_SAMPLE_RATE
    assert waveform is not None
    assert waveform.dtype == np.dtype("float32")
    assert len(waveform.shape) == 2
    assert waveform.shape[0] == TEST_EXPECTED_SAMPLES
    assert waveform.shape[1] == 2


def test_load_error(adapter):
    """Test load ffprobe exception"""
    with raises(SpleeterError):
        adapter.load("Paris City Jazz", TEST_OFFSET, TEST_DURATION, TEST_SAMPLE_RATE)


def test_save(adapter, audio_data):
    """Test audio saving."""
    with TemporaryDirectory() as directory:
        path = join(directory, "ffmpeg-save.mp3")
        adapter.save(path, audio_data[0], audio_data[1])
        probe = ffmpeg.probe(path)
        assert len(probe["streams"]) == 1
        stream = probe["streams"][0]
        assert stream["codec_type"] == "audio"
        assert stream["channels"] == 2
        # Tolerance rather than an exact duration: mp3 encoder delay/padding is
        # reported differently across ffmpeg versions.
        assert float(stream["duration"]) == approx(TEST_EXPECTED_DURATION, abs=0.1)
