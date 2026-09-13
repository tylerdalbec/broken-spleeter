#!/usr/bin/env python
# coding: utf8

"""
Unit tests for the `python -m broken` command-line helpers.

Covers argument parsing and the sweep checks that run before any model is
built. No checkpoint download and no rendering.
"""

import argparse
import json
import tempfile
from pathlib import Path

import pytest

from broken.__main__ import (
    main,
    parse_fixed_params,
    parse_param_value,
    resolve_audio_window,
    variation_label,
)
from broken.recipe import Recipe

AUDIO = "audio_example.mp3"


@pytest.fixture
def tmp_dir():
    """Temporary directory via `tempfile`, matching the other broken tests."""
    with tempfile.TemporaryDirectory() as directory:
        yield Path(directory)


def test_parse_param_value_types():
    """Verify strings parse into each parameter's declared type."""
    assert parse_param_value("time_shift", "frames", "-4") == -4
    assert parse_param_value("contrast", "gamma", "0.5") == 0.5
    assert parse_param_value("time_shift", "wrap", "TRUE") is True
    assert parse_param_value("freq_shift", "wrap", "false") is False
    assert parse_param_value("noise", "seed", "7") == 7


def test_parse_param_value_invalid():
    """Verify unknown params, bad numbers and loose booleans raise."""
    with pytest.raises(ValueError, match="unknown param"):
        parse_param_value("quantize", "seed", "1")
    with pytest.raises(ValueError, match="invalid value"):
        parse_param_value("quantize", "levels", "2.5")
    with pytest.raises(ValueError, match="true or false"):
        parse_param_value("time_shift", "wrap", "yes")


def test_parse_fixed_params():
    """Verify --set assignments parse and malformed ones raise."""
    assert parse_fixed_params("time_shift", ["wrap=true"]) == {"wrap": True}
    assert parse_fixed_params("threshold", None) == {}
    with pytest.raises(ValueError, match="NAME=VALUE"):
        parse_fixed_params("time_shift", ["wrap"])
    with pytest.raises(ValueError, match="more than once"):
        parse_fixed_params("time_shift", ["wrap=true", "wrap=false"])


def test_variation_label_ms():
    """Verify millisecond labels keep requested values that share a frame apart."""
    assert variation_label("quantize", "levels", 8) == "quantize.levels=8"
    zero = variation_label("time_shift", "frames", 0, 0.0)
    ten = variation_label("time_shift", "frames", 0, 10.0)
    assert zero == "time_shift.frames=0_0ms"
    assert ten == "time_shift.frames=0_10ms"


def test_resolve_audio_window_precedence():
    """Verify flags beat the recipe, and the recipe beats defaults."""
    recipe = Recipe(offset=30.0, duration=15.0)
    flags = argparse.Namespace(offset=5.0, duration=None)
    assert resolve_audio_window(flags, recipe) == (5.0, 15.0)
    none = argparse.Namespace(offset=None, duration=None)
    assert resolve_audio_window(none, None) == (0.0, 600.0)


def _write_recipe(path: Path, data: dict) -> str:
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_sweep_rejects_disabled_base_recipe(tmp_dir, capsys):
    """Verify sweeping onto a disabled base recipe fails instead of bypassing."""
    base = _write_recipe(tmp_dir / "base.json", {"mask": {"enabled": False}})
    code = main(
        [
            "sweep",
            AUDIO,
            "--op",
            "quantize",
            "--param",
            "levels",
            "--values",
            "2,4",
            "--recipe",
            base,
            "-o",
            str(tmp_dir / "out"),
        ]
    )
    assert code == 1
    assert "mask.enabled false" in capsys.readouterr().err
    assert not (tmp_dir / "out").exists()


def test_sweep_rejects_duplicate_variations(tmp_dir, capsys):
    """Verify values that would overwrite each other's output are rejected."""
    code = main(
        [
            "sweep",
            AUDIO,
            "--op",
            "contrast",
            "--param",
            "gamma",
            "--values",
            "0.5,.5",
            "-o",
            str(tmp_dir / "out"),
        ]
    )
    assert code == 1
    assert "duplicate variations" in capsys.readouterr().err


def test_sweep_rejects_param_both_swept_and_fixed(tmp_dir, capsys):
    """Verify a parameter cannot be swept and fixed at once."""
    code = main(
        [
            "sweep",
            AUDIO,
            "--op",
            "time_shift",
            "--param",
            "frames",
            "--values",
            "1,2",
            "--set",
            "frames=3",
            "-o",
            str(tmp_dir / "out"),
        ]
    )
    assert code == 1
    assert "both swept and fixed" in capsys.readouterr().err


def test_sweep_reports_missing_required_param(tmp_dir, capsys):
    """Verify sweeping one param of an op with other required params fails early."""
    code = main(
        [
            "sweep",
            AUDIO,
            "--op",
            "noise",
            "--param",
            "seed",
            "--values",
            "1,2",
            "-o",
            str(tmp_dir / "out"),
        ]
    )
    assert code == 1
    assert "Missing required parameter" in capsys.readouterr().err
    assert not (tmp_dir / "out").exists()
