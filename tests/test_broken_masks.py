#!/usr/bin/env python
# coding: utf8

"""
Unit tests for mask corruption operations and recipe representations.

Fast, pure NumPy tests without model loading, network calls, or audio files.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from broken.masks import (
    complement_blend,
    contrast,
    freq_shift,
    gain_bias,
    noise,
    quantize,
    threshold,
    time_shift,
)
from broken.recipe import MaskConfig, MaskOp, Recipe, load_recipe, save_recipe

# ---------------------------------------------------------------------------
# Mask Operations Tests
# ---------------------------------------------------------------------------


def test_contrast_arithmetic():
    """Verify sign-preserving contrast power law arithmetic."""
    mask = np.array([-0.5, 0.0, 0.25, 1.0], dtype=np.float32).reshape(2, 2, 1)
    # gamma = 2.0
    out = contrast(mask, gamma=2.0)
    expected = np.array([-0.25, 0.0, 0.0625, 1.0], dtype=np.float32).reshape(2, 2, 1)
    np.testing.assert_allclose(out, expected, rtol=1e-5)

    # gamma = 0.5
    out_half = contrast(mask, gamma=0.5)
    expected_half = np.array([-np.sqrt(0.5), 0.0, 0.5, 1.0], dtype=np.float32).reshape(
        2, 2, 1
    )
    np.testing.assert_allclose(out_half, expected_half, rtol=1e-5)


def test_contrast_dtype_and_purity():
    """Verify float32 return dtype and input immutability."""
    mask = np.array([0.2, 0.8], dtype=np.float32).reshape(2, 1, 1)
    orig = mask.copy()
    out = contrast(mask, gamma=1.5)
    assert out.dtype == np.float32
    assert out is not mask
    np.testing.assert_array_equal(mask, orig)


def test_contrast_invalid():
    """Verify that non-positive gamma raises ValueError."""
    mask = np.ones((2, 2, 1), dtype=np.float32)
    with pytest.raises(ValueError, match="gamma must be positive"):
        contrast(mask, gamma=0.0)
    with pytest.raises(ValueError, match="gamma must be positive"):
        contrast(mask, gamma=-1.5)


def test_gain_bias_arithmetic():
    """Verify affine scale and offset."""
    mask = np.array([0.0, 0.5, 1.0], dtype=np.float32).reshape(3, 1, 1)
    orig = mask.copy()
    out = gain_bias(mask, gain=2.0, bias=-0.5)
    expected = np.array([-0.5, 0.5, 1.5], dtype=np.float32).reshape(3, 1, 1)
    np.testing.assert_allclose(out, expected, rtol=1e-5)
    assert out.dtype == np.float32
    np.testing.assert_array_equal(mask, orig)


def test_threshold_hard():
    """Verify hard thresholding when softness == 0.0."""
    mask = np.array([0.2, 0.5, 0.8], dtype=np.float32).reshape(3, 1, 1)
    orig = mask.copy()
    out = threshold(mask, threshold=0.5, softness=0.0)
    expected = np.array([0.0, 1.0, 1.0], dtype=np.float32).reshape(3, 1, 1)
    np.testing.assert_allclose(out, expected)
    assert out.dtype == np.float32
    np.testing.assert_array_equal(mask, orig)


def test_threshold_soft():
    """Verify soft linear ramp thresholding when softness > 0.0."""
    # formula: clip((M - threshold) / softness + 0.5, 0, 1)
    mask = np.array([0.1, 0.3, 0.5, 0.7, 0.9], dtype=np.float32).reshape(5, 1, 1)
    out = threshold(mask, threshold=0.5, softness=0.4)
    # 0.1 -> (0.1 - 0.5)/0.4 + 0.5 = -0.5 -> clip -> 0.0
    # 0.3 -> (0.3 - 0.5)/0.4 + 0.5 = 0.0
    # 0.5 -> (0.5 - 0.5)/0.4 + 0.5 = 0.5
    # 0.7 -> (0.7 - 0.5)/0.4 + 0.5 = 1.0
    # 0.9 -> (0.9 - 0.5)/0.4 + 0.5 = 1.5 -> clip -> 1.0
    expected = np.array([0.0, 0.0, 0.5, 1.0, 1.0], dtype=np.float32).reshape(5, 1, 1)
    np.testing.assert_allclose(out, expected, rtol=1e-5, atol=1e-6)
    assert out.dtype == np.float32


def test_threshold_invalid():
    """Verify negative softness raises ValueError."""
    mask = np.ones((2, 2, 1), dtype=np.float32)
    with pytest.raises(ValueError, match="softness must be non-negative"):
        threshold(mask, threshold=0.5, softness=-0.1)


def test_quantize_levels_2():
    """Verify quantization with levels = 2."""
    mask = np.array([0.0, 0.4, 0.6, 1.0], dtype=np.float32).reshape(4, 1, 1)
    orig = mask.copy()
    out = quantize(mask, levels=2)
    expected = np.array([0.0, 0.0, 1.0, 1.0], dtype=np.float32).reshape(4, 1, 1)
    np.testing.assert_allclose(out, expected)
    assert out.dtype == np.float32
    np.testing.assert_array_equal(mask, orig)


def test_quantize_even_division():
    """Verify quantization with levels dividing evenly (e.g. 5 levels)."""
    mask = np.array([0.0, 0.12, 0.26, 0.74, 0.88, 1.0], dtype=np.float32).reshape(
        6, 1, 1
    )
    out = quantize(mask, levels=5)
    expected = np.array([0.0, 0.0, 0.25, 0.75, 1.0, 1.0], dtype=np.float32).reshape(
        6, 1, 1
    )
    np.testing.assert_allclose(out, expected, rtol=1e-5)
    assert out.dtype == np.float32


def test_quantize_invalid():
    """Verify that levels < 2 or non-integer raises ValueError."""
    mask = np.ones((2, 2, 1), dtype=np.float32)
    with pytest.raises(ValueError, match="levels must be an integer >= 2"):
        quantize(mask, levels=1)
    with pytest.raises(ValueError, match="levels must be an integer >= 2"):
        quantize(mask, levels=0)
    with pytest.raises(ValueError, match="levels must be an integer >= 2"):
        quantize(mask, levels=2.5)  # type: ignore


def test_time_shift():
    """Verify time_shift along axis 0 in both directions with wrap False and True."""
    # 4 frames, 2 bins, 1 channel
    mask = np.arange(8, dtype=np.float32).reshape(4, 2, 1)
    orig = mask.copy()

    # Zero shift
    out_zero = time_shift(mask, frames=0)
    np.testing.assert_array_equal(out_zero, mask)
    assert out_zero is not mask

    # Positive shift, wrap=False
    out_p_nowrap = time_shift(mask, frames=1, wrap=False)
    assert np.all(out_p_nowrap[0] == 0.0)
    np.testing.assert_array_equal(out_p_nowrap[1:], mask[:-1])

    # Positive shift, wrap=True
    out_p_wrap = time_shift(mask, frames=1, wrap=True)
    np.testing.assert_array_equal(out_p_wrap[0], mask[-1])
    np.testing.assert_array_equal(out_p_wrap[1:], mask[:-1])

    # Negative shift, wrap=False
    out_n_nowrap = time_shift(mask, frames=-1, wrap=False)
    assert np.all(out_n_nowrap[-1] == 0.0)
    np.testing.assert_array_equal(out_n_nowrap[:-1], mask[1:])

    # Negative shift, wrap=True
    out_n_wrap = time_shift(mask, frames=-1, wrap=True)
    np.testing.assert_array_equal(out_n_wrap[-1], mask[0])
    np.testing.assert_array_equal(out_n_wrap[:-1], mask[1:])

    # Shifts exceeding axis length
    out_huge_nowrap = time_shift(mask, frames=10, wrap=False)
    np.testing.assert_array_equal(out_huge_nowrap, np.zeros_like(mask))

    out_huge_neg_nowrap = time_shift(mask, frames=-10, wrap=False)
    np.testing.assert_array_equal(out_huge_neg_nowrap, np.zeros_like(mask))

    out_huge_wrap = time_shift(mask, frames=5, wrap=True)  # 5 % 4 = 1
    np.testing.assert_array_equal(out_huge_wrap, out_p_wrap)

    assert out_p_nowrap.dtype == np.float32
    np.testing.assert_array_equal(mask, orig)

    with pytest.raises(ValueError, match="frames must be an integer"):
        time_shift(mask, frames="four")  # type: ignore


def test_freq_shift():
    """Verify freq_shift along axis 1 in both directions with wrap False and True."""
    # 2 frames, 4 bins, 1 channel
    mask = np.arange(8, dtype=np.float32).reshape(2, 4, 1)
    orig = mask.copy()

    # Zero shift
    out_zero = freq_shift(mask, bins=0)
    np.testing.assert_array_equal(out_zero, mask)

    # Positive shift, wrap=False (raises frequency: index 0 is 0, rest shifted right)
    out_p_nowrap = freq_shift(mask, bins=1, wrap=False)
    assert np.all(out_p_nowrap[:, 0, :] == 0.0)
    np.testing.assert_array_equal(out_p_nowrap[:, 1:, :], mask[:, :-1, :])

    # Positive shift, wrap=True
    out_p_wrap = freq_shift(mask, bins=1, wrap=True)
    np.testing.assert_array_equal(out_p_wrap[:, 0, :], mask[:, -1, :])
    np.testing.assert_array_equal(out_p_wrap[:, 1:, :], mask[:, :-1, :])

    # Negative shift, wrap=False (lowers frequency: top bin is 0)
    out_n_nowrap = freq_shift(mask, bins=-1, wrap=False)
    assert np.all(out_n_nowrap[:, -1, :] == 0.0)
    np.testing.assert_array_equal(out_n_nowrap[:, :-1, :], mask[:, 1:, :])

    # Negative shift, wrap=True
    out_n_wrap = freq_shift(mask, bins=-1, wrap=True)
    np.testing.assert_array_equal(out_n_wrap[:, -1, :], mask[:, 0, :])
    np.testing.assert_array_equal(out_n_wrap[:, :-1, :], mask[:, 1:, :])

    # Shifts exceeding axis length
    out_huge_nowrap = freq_shift(mask, bins=10, wrap=False)
    np.testing.assert_array_equal(out_huge_nowrap, np.zeros_like(mask))

    out_huge_neg_nowrap = freq_shift(mask, bins=-10, wrap=False)
    np.testing.assert_array_equal(out_huge_neg_nowrap, np.zeros_like(mask))

    out_huge_wrap = freq_shift(mask, bins=5, wrap=True)  # 5 % 4 = 1
    np.testing.assert_array_equal(out_huge_wrap, out_p_wrap)

    assert out_p_nowrap.dtype == np.float32
    np.testing.assert_array_equal(mask, orig)

    with pytest.raises(ValueError, match="bins must be an integer"):
        freq_shift(mask, bins=1.5)  # type: ignore


def test_complement_blend():
    """Verify complement blend arithmetic."""
    mask = np.array([0.0, 0.2, 0.8, 1.0], dtype=np.float32).reshape(4, 1, 1)
    orig = mask.copy()

    # amount = 0.0 -> identity
    out_0 = complement_blend(mask, amount=0.0)
    np.testing.assert_allclose(out_0, mask)

    # amount = 1.0 -> full inversion
    out_1 = complement_blend(mask, amount=1.0)
    np.testing.assert_allclose(out_1, 1.0 - mask)

    # amount = 0.5 -> flat 0.5
    out_half = complement_blend(mask, amount=0.5)
    np.testing.assert_allclose(out_half, np.full_like(mask, 0.5))

    assert out_1.dtype == np.float32
    np.testing.assert_array_equal(mask, orig)


def test_noise():
    """Verify Gaussian noise repeatability with seed and divergence."""
    mask = np.zeros((10, 10, 2), dtype=np.float32)
    orig = mask.copy()

    out1 = noise(mask, amount=0.1, seed=42)
    out2 = noise(mask, amount=0.1, seed=42)
    out3 = noise(mask, amount=0.1, seed=99)

    assert out1.dtype == np.float32
    np.testing.assert_array_equal(out1, out2)
    assert not np.array_equal(out1, out3)
    np.testing.assert_array_equal(mask, orig)

    with pytest.raises(ValueError, match="seed must be an integer"):
        noise(mask, amount=0.1, seed="bad")  # type: ignore


# ---------------------------------------------------------------------------
# Recipe Representation and Validation Tests
# ---------------------------------------------------------------------------


def test_recipe_roundtrip():
    """Verify Recipe -> dict -> JSON -> dict -> Recipe lossless round-trip."""
    rec = Recipe(
        version=1,
        model="spleeter:2stems",
        seed=1847,
        mask=MaskConfig(
            enabled=True,
            clamp=False,
            ops=[
                MaskOp(op="quantize", params={"levels": 8}),
                MaskOp(op="time_shift", params={"frames": 4, "wrap": True}),
                MaskOp(op="noise", params={"amount": 0.05}, seed=123),
            ],
        ),
    )

    d = rec.to_dict()
    json_str = json.dumps(d)
    d_loaded = json.loads(json_str)
    rec2 = Recipe.from_dict(d_loaded)

    assert rec2.to_dict() == d
    assert rec2.version == 1
    assert rec2.model == "spleeter:2stems"
    assert rec2.seed == 1847
    assert len(rec2.mask.ops) == 3
    assert rec2.mask.ops[0].op == "quantize"
    assert rec2.mask.ops[0].params["levels"] == 8
    assert rec2.mask.ops[1].params["wrap"] is True
    assert rec2.mask.ops[2].seed == 123


def test_recipe_file_io():
    """Verify save_recipe and load_recipe file helpers."""
    rec = Recipe(
        version=1,
        model="spleeter:4stems",
        seed=42,
        mask=MaskConfig(
            enabled=True,
            clamp=True,
            ops=[MaskOp(op="contrast", params={"gamma": 1.5})],
        ),
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_file = Path(tmp_dir) / "sub" / "recipe.json"
        save_recipe(rec, target_file)
        assert target_file.exists()

        loaded = load_recipe(target_file)
        assert loaded.to_dict() == rec.to_dict()


def test_recipe_validation_unknown_op():
    """Verify that an unknown op name raises ValueError."""
    data = {
        "version": 1,
        "mask": {"ops": [{"op": "blur", "radius": 3}]},
    }
    with pytest.raises(ValueError, match="Unknown mask operation"):
        Recipe.from_dict(data)


def test_recipe_validation_unknown_param():
    """Verify that an unknown parameter raises ValueError."""
    data = {
        "version": 1,
        "mask": {"ops": [{"op": "quantize", "levels": 4, "extra": 10}]},
    }
    with pytest.raises(ValueError, match="Unknown parameter"):
        Recipe.from_dict(data)


def test_recipe_validation_missing_param():
    """Verify that missing required parameter raises ValueError."""
    data = {
        "version": 1,
        "mask": {"ops": [{"op": "contrast"}]},
    }
    with pytest.raises(ValueError, match="Missing required parameter"):
        Recipe.from_dict(data)


def test_recipe_validation_out_of_domain():
    """Verify that out-of-domain parameter values raise ValueError."""
    # levels < 2
    with pytest.raises(ValueError, match="levels for op 'quantize' must be >= 2"):
        Recipe.from_dict({"mask": {"ops": [{"op": "quantize", "levels": 1}]}})

    # gamma <= 0
    with pytest.raises(ValueError, match="gamma for op 'contrast' must be positive"):
        Recipe.from_dict({"mask": {"ops": [{"op": "contrast", "gamma": -0.5}]}})

    # softness < 0
    with pytest.raises(
        ValueError, match="softness for op 'threshold' must be non-negative"
    ):
        Recipe.from_dict(
            {"mask": {"ops": [{"op": "threshold", "threshold": 0.5, "softness": -0.1}]}}
        )


def test_recipe_deterministic_seeding():
    """Verify deterministic op seed derivation from recipe seed and op index."""
    mask = np.zeros((4, 4, 1), dtype=np.float32)
    rec = Recipe(
        seed=1847,
        mask=MaskConfig(
            enabled=True,
            ops=[
                MaskOp(op="noise", params={"amount": 0.1}),
                MaskOp(op="noise", params={"amount": 0.1}),
            ],
        ),
    )
    # The two noise ops at index 0 and 1 must produce different realizations
    out_op0 = rec._execute_op(mask, rec.mask.ops[0], 0)
    out_op1 = rec._execute_op(mask, rec.mask.ops[1], 1)
    assert not np.array_equal(out_op0, out_op1)

    # Applying the recipe multiple times must be bitwise reproducible
    res1 = rec.apply_to_mask(mask)
    res2 = rec.apply_to_mask(mask)
    np.testing.assert_array_equal(res1, res2)


def test_recipe_bypass_and_clamp():
    """Verify is_bypass property and end-of-chain clamp."""
    # Disabled mask -> is_bypass True
    rec_disabled = Recipe(
        mask=MaskConfig(
            enabled=False, ops=[MaskOp(op="quantize", params={"levels": 2})]
        )
    )
    assert rec_disabled.is_bypass is True

    # Empty ops -> is_bypass True
    rec_empty = Recipe(mask=MaskConfig(enabled=True, ops=[]))
    assert rec_empty.is_bypass is True

    # Clamp = True
    mask = np.array([-0.5, 0.5, 1.5], dtype=np.float32).reshape(3, 1, 1)
    rec_clamp = Recipe(
        mask=MaskConfig(
            enabled=True,
            clamp=True,
            ops=[MaskOp(op="gain_bias", params={"gain": 1.0, "bias": 0.0})],
        )
    )
    out_clamped = rec_clamp.apply_to_mask(mask)
    expected_clamped = np.array([0.0, 0.5, 1.0], dtype=np.float32).reshape(3, 1, 1)
    np.testing.assert_allclose(out_clamped, expected_clamped)

    # Clamp = False: out of [0, 1] preserved
    rec_noclamp = Recipe(
        mask=MaskConfig(
            enabled=True,
            clamp=False,
            ops=[MaskOp(op="gain_bias", params={"gain": 1.0, "bias": 0.0})],
        )
    )
    out_unclamped = rec_noclamp.apply_to_mask(mask)
    np.testing.assert_allclose(out_unclamped, mask)


def test_noise_matches_brief_formula():
    """Verify noise draws the default float64 normal stream, then casts."""
    mask = np.full((3, 4, 2), 0.5, dtype=np.float32)
    rng = np.random.default_rng(42)
    expected = (mask + 0.1 * rng.standard_normal(mask.shape)).astype(np.float32)
    np.testing.assert_array_equal(noise(mask, amount=0.1, seed=42), expected)


def test_recipe_noise_without_seed_roundtrip():
    """Verify a noise op without its own seed survives save and reload."""
    rec = Recipe.from_dict(
        {"seed": 5, "mask": {"ops": [{"op": "noise", "amount": 0.1}]}}
    )
    d = rec.to_dict()
    assert "seed" not in d["mask"]["ops"][0]
    rec2 = Recipe.from_dict(json.loads(json.dumps(d)))
    assert rec2.to_dict() == d
    assert rec2.mask.ops[0].seed is None


def test_recipe_seed_only_on_noise():
    """Verify a seed on an operation that is not stochastic raises."""
    with pytest.raises(ValueError, match="Unknown parameter"):
        Recipe.from_dict(
            {"mask": {"ops": [{"op": "quantize", "levels": 4, "seed": 1}]}}
        )


def test_recipe_explicit_op_seed_wins():
    """Verify an explicit per-op seed overrides the derived one."""
    mask = np.zeros((4, 4, 1), dtype=np.float32)
    rec = Recipe.from_dict(
        {"seed": 1847, "mask": {"ops": [{"op": "noise", "amount": 0.1, "seed": 7}]}}
    )
    np.testing.assert_array_equal(
        rec.apply_to_mask(mask), noise(mask, amount=0.1, seed=7)
    )


def test_recipe_audio_window():
    """Verify the optional audio excerpt round-trips and validates."""
    rec = Recipe.from_dict({"audio": {"offset": 30, "duration": 12.5}})
    assert (rec.offset, rec.duration) == (30.0, 12.5)
    assert Recipe.from_dict(rec.to_dict()).to_dict() == rec.to_dict()
    assert "audio" not in Recipe().to_dict()
    with pytest.raises(ValueError, match="non-negative"):
        Recipe.from_dict({"audio": {"offset": -1}})
    with pytest.raises(ValueError, match="positive"):
        Recipe.from_dict({"audio": {"duration": 0}})
    with pytest.raises(ValueError, match="Unknown key"):
        Recipe.from_dict({"audio": {"start": 1}})
