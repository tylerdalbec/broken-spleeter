#!/usr/bin/env python
# coding: utf8

"""
Mask corruption operations.

Every operation takes and returns a mask array shaped `(frames, bins,
channels)`, float32, nominally in `[0.0, 1.0]`. Operations are pure: they do
not modify their input.
"""

from typing import Optional

# pyright: reportMissingImports=false
# pylint: disable=import-error
import numpy as np

# pylint: enable=import-error


def contrast(mask: np.ndarray, gamma: float) -> np.ndarray:
    """
    Apply sign-preserving power-law contrast to the mask.

    Computes `sign(M) * abs(M) ** gamma`. Sign-preserving so that composing
    after an operation that produced negatives does not yield NaN.

    Parameters:
        mask (np.ndarray):
            Mask shaped `(frames, bins, channels)`.
        gamma (float):
            Exponent for the power law. Must be strictly positive.

    Returns:
        np.ndarray:
            Contrast-adjusted mask, float32, same shape as input.

    Raises:
        ValueError:
            If gamma is not positive.
    """
    if gamma <= 0:
        raise ValueError(f"gamma must be positive, got {gamma}")
    return (np.sign(mask) * (np.abs(mask) ** gamma)).astype(np.float32)


def gain_bias(mask: np.ndarray, gain: float = 1.0, bias: float = 0.0) -> np.ndarray:
    """
    Apply affine scale and offset: `gain * mask + bias`.

    Parameters:
        mask (np.ndarray):
            Mask shaped `(frames, bins, channels)`.
        gain (float):
            (Optional) Scaling factor, defaults to 1.0.
        bias (float):
            (Optional) Offset added after scaling, defaults to 0.0.

    Returns:
        np.ndarray:
            Scaled and offset mask, float32, same shape as input.
    """
    return (gain * mask + bias).astype(np.float32)


def threshold(mask: np.ndarray, threshold: float, softness: float = 0.0) -> np.ndarray:
    """
    Apply hard or soft thresholding to the mask.

    When `softness == 0.0`, performs hard binarization `(mask >= threshold)` as
    float32. When `softness > 0.0`, applies a linear ramp clipped to [0, 1]:
    `clip((mask - threshold) / softness + 0.5, 0, 1)`.

    Parameters:
        mask (np.ndarray):
            Mask shaped `(frames, bins, channels)`.
        threshold (float):
            Center value for the threshold.
        softness (float):
            (Optional) Width of transition window. Must be non-negative.
            Defaults to 0.0 (hard threshold).

    Returns:
        np.ndarray:
            Thresholded mask, float32, same shape as input.

    Raises:
        ValueError:
            If softness is negative.
    """
    if softness < 0.0:
        raise ValueError(f"softness must be non-negative, got {softness}")
    if softness == 0.0:
        return (mask >= threshold).astype(np.float32)
    ramp = (mask - threshold) / softness + 0.5
    return np.clip(ramp, 0.0, 1.0).astype(np.float32)


def quantize(mask: np.ndarray, levels: int) -> np.ndarray:
    """
    Quantize mask values into discrete uniformly spaced levels in [0, 1].

    Computes `round(mask * (levels - 1)) / (levels - 1)`.

    Parameters:
        mask (np.ndarray):
            Mask shaped `(frames, bins, channels)`.
        levels (int):
            Number of discrete levels. Must be an integer >= 2.

    Returns:
        np.ndarray:
            Quantized mask, float32, same shape as input.

    Raises:
        ValueError:
            If levels is not an integer >= 2.
    """
    if not isinstance(levels, (int, np.integer)) or levels < 2:
        raise ValueError(f"levels must be an integer >= 2, got {levels}")
    step = levels - 1
    return (np.round(mask * step) / step).astype(np.float32)


def time_shift(mask: np.ndarray, frames: int, wrap: bool = False) -> np.ndarray:
    """
    Displace a mask along the time axis (axis 0).

    The model's classification from one moment is applied to another, which
    detaches mask transitions from the events that caused them.

    Parameters:
        mask (np.ndarray):
            Mask shaped `(frames, bins, channels)`.
        frames (int):
            Displacement in STFT frames. Positive delays the mask, negative
            advances it.
        wrap (bool):
            (Optional) If True, rolls values folding displaced edges around.
            If False (default), fills vacated positions with zeros.

    Returns:
        np.ndarray:
            Displaced mask, float32, same shape as input.

    Raises:
        ValueError:
            If frames is not an integer.
    """
    if not isinstance(frames, (int, np.integer)):
        raise ValueError(f"frames must be an integer, got {frames}")
    frames = int(frames)
    if frames == 0:
        return mask.copy().astype(np.float32)
    if wrap:
        return np.roll(mask, frames, axis=0).astype(np.float32)
    n_frames = mask.shape[0]
    if abs(frames) >= n_frames:
        return np.zeros_like(mask, dtype=np.float32)
    out = np.zeros_like(mask, dtype=np.float32)
    if frames > 0:
        out[frames:] = mask[:-frames]
    else:
        out[:frames] = mask[-frames:]
    return out.astype(np.float32)


def freq_shift(mask: np.ndarray, bins: int, wrap: bool = False) -> np.ndarray:
    """
    Displace a mask along the frequency axis (axis 1).

    Parameters:
        mask (np.ndarray):
            Mask shaped `(frames, bins, channels)`.
        bins (int):
            Displacement in frequency bins. Positive raises frequencies,
            negative lowers them.
        wrap (bool):
            (Optional) If True, rolls values folding displaced edges around.
            If False (default), fills vacated positions with zeros.

    Returns:
        np.ndarray:
            Displaced mask, float32, same shape as input.

    Raises:
        ValueError:
            If bins is not an integer.
    """
    if not isinstance(bins, (int, np.integer)):
        raise ValueError(f"bins must be an integer, got {bins}")
    bins = int(bins)
    if bins == 0:
        return mask.copy().astype(np.float32)
    if wrap:
        return np.roll(mask, bins, axis=1).astype(np.float32)
    n_bins = mask.shape[1]
    if abs(bins) >= n_bins:
        return np.zeros_like(mask, dtype=np.float32)
    out = np.zeros_like(mask, dtype=np.float32)
    if bins > 0:
        out[:, bins:, :] = mask[:, :-bins, :]
    else:
        out[:, :bins, :] = mask[:, -bins:, :]
    return out.astype(np.float32)


def complement_blend(mask: np.ndarray, amount: float) -> np.ndarray:
    """
    Blend mask with its complement: `(1 - amount) * M + amount * (1 - M)`.

    At `amount = 1.0` this produces full inversion; at `amount = 0.5` it
    produces a flat 0.5 mask; at `amount = 0.0` it leaves the mask untouched.

    Parameters:
        mask (np.ndarray):
            Mask shaped `(frames, bins, channels)`.
        amount (float):
            Blend factor between original and inverted mask.

    Returns:
        np.ndarray:
            Blended mask, float32, same shape as input.
    """
    return ((1.0 - amount) * mask + amount * (1.0 - mask)).astype(np.float32)


def noise(mask: np.ndarray, amount: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Add zero-mean Gaussian noise to mask values.

    Computes `mask + amount * rng.standard_normal(mask.shape)`.

    Parameters:
        mask (np.ndarray):
            Mask shaped `(frames, bins, channels)`.
        amount (float):
            Standard deviation scaling factor for normal noise.
        seed (Optional[int]):
            (Optional) Random generator seed for reproducibility.

    Returns:
        np.ndarray:
            Noisy mask, float32, same shape as input.

    Raises:
        ValueError:
            If seed is provided and is not an integer.
    """
    if seed is not None and not isinstance(seed, (int, np.integer)):
        raise ValueError(f"seed must be an integer, got {seed}")
    rng = np.random.default_rng(seed)
    return (mask + amount * rng.standard_normal(mask.shape)).astype(np.float32)
