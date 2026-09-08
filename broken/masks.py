#!/usr/bin/env python
# coding: utf8

"""
Mask corruption operations.

Every operation takes and returns a mask array shaped `(frames, bins,
channels)`, float32, nominally in `[0.0, 1.0]`. Operations are pure: they do
not modify their input.
"""

# pyright: reportMissingImports=false
# pylint: disable=import-error
import numpy as np

# pylint: enable=import-error


def time_shift(mask: np.ndarray, frames: int) -> np.ndarray:
    """
    Displace a mask along the time axis.

    The model's classification from one moment is applied to another, which
    detaches mask transitions from the events that caused them.

    Vacated frames are filled with zeros rather than wrapped, so a shift
    removes material at one edge instead of folding it around. That choice is
    provisional; wrapping is a plausible alternative worth auditioning.

    Parameters:
        mask (np.ndarray):
            Mask shaped `(frames, bins, channels)`.
        frames (int):
            Displacement in STFT frames. Positive delays the mask, negative
            advances it.

    Returns:
        np.ndarray:
            Displaced mask, same shape and dtype as the input.
    """
    if frames == 0:
        return mask.copy()
    out = np.zeros_like(mask)
    if frames > 0:
        out[frames:] = mask[:-frames]
    else:
        out[:frames] = mask[-frames:]
    return out
