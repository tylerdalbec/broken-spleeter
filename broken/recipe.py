#!/usr/bin/env python
# coding: utf8

"""
Recipe representation and execution for mask corruption.

A recipe is a plain JSON document describing one complete mask corruption.
Operations are ordered and executed sequentially. Seeding is deterministic:
an explicit per-operation seed takes precedence; otherwise seeds are derived
from the recipe seed and the operation's index in the chain.

Reordering or inserting operations changes derived seeds; an explicit per-op
seed provides an escape hatch when invariant noise realizations are needed.
"""

import copy
import json
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

# pyright: reportMissingImports=false
# pylint: disable=import-error
import numpy as np

# pylint: enable=import-error
from . import masks

OP_SPECS: Dict[str, Dict[str, Any]] = {
    "contrast": {
        "required": {"gamma"},
        "optional": set(),
        "types": {"gamma": (int, float)},
    },
    "gain_bias": {
        "required": set(),
        "optional": {"gain", "bias"},
        "types": {"gain": (int, float), "bias": (int, float)},
        "defaults": {"gain": 1.0, "bias": 0.0},
    },
    "threshold": {
        "required": {"threshold"},
        "optional": {"softness"},
        "types": {"threshold": (int, float), "softness": (int, float)},
        "defaults": {"softness": 0.0},
    },
    "quantize": {
        "required": {"levels"},
        "optional": set(),
        "types": {"levels": (int, np.integer)},
    },
    "time_shift": {
        "required": {"frames"},
        "optional": {"wrap"},
        "types": {"frames": (int, np.integer), "wrap": bool},
        "defaults": {"wrap": False},
    },
    "freq_shift": {
        "required": {"bins"},
        "optional": {"wrap"},
        "types": {"bins": (int, np.integer), "wrap": bool},
        "defaults": {"wrap": False},
    },
    "complement_blend": {
        "required": {"amount"},
        "optional": set(),
        "types": {"amount": (int, float)},
    },
    "noise": {
        "required": {"amount"},
        "optional": set(),
        "types": {"amount": (int, float)},
        "seeded": True,
    },
}


def derive_op_seed(recipe_seed: Optional[int], op_index: int) -> int:
    """
    Derive a deterministic 32-bit unsigned integer seed for an operation.

    Uses `np.random.SeedSequence([recipe_seed, op_index])`.

    Note: Reordering or inserting operations in a recipe changes the index and
    thus changes the derived seed. This is expected; specify an explicit
    per-operation `"seed"` when order-independent reproducibility is required.
    """
    base_seed = recipe_seed if recipe_seed is not None else 0
    seq = np.random.SeedSequence([base_seed, op_index])
    return int(seq.generate_state(1)[0])


@dataclass
class MaskOp:
    """Single mask corruption operation specification."""

    op: str
    params: Dict[str, Any] = field(default_factory=dict)
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary representation."""
        result: Dict[str, Any] = {"op": self.op}
        result.update(self.params)
        if self.seed is not None:
            result["seed"] = self.seed
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MaskOp":
        """
        Validate and construct a MaskOp from dictionary.

        Raises:
            ValueError:
                If op name is unknown, parameters are invalid, or values are
                out of domain.
        """
        if not isinstance(data, dict):
            raise ValueError(f"Operation entry must be a dict, got {type(data)}")
        if "op" not in data:
            raise ValueError(f"Operation entry missing required 'op' field: {data}")
        op_name = data["op"]
        if op_name not in OP_SPECS:
            raise ValueError(
                f"Unknown mask operation: '{op_name}'. Allowed operations: "
                f"{sorted(OP_SPECS.keys())}"
            )

        spec = OP_SPECS[op_name]
        allowed_keys: Set[str] = {"op"} | spec["required"] | spec["optional"]
        if spec.get("seeded"):
            allowed_keys.add("seed")
        unknown_keys = set(data.keys()) - allowed_keys
        if unknown_keys:
            raise ValueError(
                f"Unknown parameter(s) {sorted(unknown_keys)} for op '{op_name}'"
            )

        missing_required = spec["required"] - set(data.keys())
        if missing_required:
            raise ValueError(
                f"Missing required parameter(s) {sorted(missing_required)} for "
                f"op '{op_name}'"
            )

        params: Dict[str, Any] = {}
        for k in spec["required"] | spec["optional"]:
            if k in data:
                val = data[k]
                expected_type = spec["types"][k]
                if expected_type is bool:
                    if not isinstance(val, bool):
                        raise ValueError(
                            f"Parameter '{k}' for op '{op_name}' must be bool, "
                            f"got {type(val)}"
                        )
                elif expected_type == (int, np.integer):
                    if isinstance(val, bool) or not isinstance(val, (int, np.integer)):
                        raise ValueError(
                            f"Parameter '{k}' for op '{op_name}' must be integer, "
                            f"got {type(val)}"
                        )
                elif expected_type == (int, float):
                    if isinstance(val, bool) or not isinstance(val, (int, float)):
                        raise ValueError(
                            f"Parameter '{k}' for op '{op_name}' must be numeric, "
                            f"got {type(val)}"
                        )
                params[k] = val
            elif "defaults" in spec and k in spec["defaults"]:
                params[k] = spec["defaults"][k]

        seed_val = data.get("seed")
        if seed_val is not None:
            if isinstance(seed_val, bool) or not isinstance(
                seed_val, (int, np.integer)
            ):
                raise ValueError(
                    f"Parameter 'seed' for op '{op_name}' must be integer, "
                    f"got {type(seed_val)}"
                )
            seed_val = int(seed_val)

        # Domain checks
        if op_name == "contrast" and params["gamma"] <= 0:
            raise ValueError(
                f"gamma for op 'contrast' must be positive, got {params['gamma']}"
            )
        if op_name == "quantize" and params["levels"] < 2:
            raise ValueError(
                f"levels for op 'quantize' must be >= 2, got {params['levels']}"
            )
        if op_name == "threshold" and params.get("softness", 0.0) < 0.0:
            raise ValueError(
                f"softness for op 'threshold' must be non-negative, got "
                f"{params.get('softness')}"
            )

        return cls(op=op_name, params=params, seed=seed_val)


@dataclass
class MaskConfig:
    """Mask manipulation pipeline configuration."""

    enabled: bool = True
    clamp: bool = False
    ops: List[MaskOp] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize mask configuration to dictionary."""
        return {
            "enabled": self.enabled,
            "clamp": self.clamp,
            "ops": [op.to_dict() for op in self.ops],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MaskConfig":
        """Validate and construct MaskConfig from dictionary."""
        if not isinstance(data, dict):
            raise ValueError(f"Mask configuration must be a dict, got {type(data)}")
        allowed_keys = {"enabled", "clamp", "ops"}
        unknown = set(data.keys()) - allowed_keys
        if unknown:
            raise ValueError(f"Unknown key(s) in mask configuration: {sorted(unknown)}")
        enabled = data.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(f"'enabled' must be a boolean, got {type(enabled)}")
        clamp = data.get("clamp", False)
        if not isinstance(clamp, bool):
            raise ValueError(f"'clamp' must be a boolean, got {type(clamp)}")
        ops_data = data.get("ops", [])
        if not isinstance(ops_data, list):
            raise ValueError(f"'ops' must be a list, got {type(ops_data)}")
        ops = [MaskOp.from_dict(op_item) for op_item in ops_data]
        return cls(enabled=enabled, clamp=clamp, ops=ops)


@dataclass
class Recipe:
    """
    Complete recipe for audio separation mask corruption.

    `offset` and `duration` record the excerpt of the input the recipe was
    rendered from, serialized under an optional `"audio"` key, so a recipe
    emitted by a sweep over an excerpt re-renders the same excerpt. Explicit
    command-line flags override them.
    """

    version: int = 1
    model: str = "spleeter:2stems"
    seed: Optional[int] = None
    mask: MaskConfig = field(default_factory=MaskConfig)
    offset: Optional[float] = None
    duration: Optional[float] = None

    @property
    def is_bypass(self) -> bool:
        """
        True if the mask corruption stage should be bypassed completely.

        When True, separation runs without feeding masks into placeholders,
        exercising the structural bypass path.
        """
        return (not self.mask.enabled) or len(self.mask.ops) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize recipe to dictionary."""
        result: Dict[str, Any] = {
            "version": self.version,
            "model": self.model,
        }
        if self.seed is not None:
            result["seed"] = self.seed
        result["mask"] = self.mask.to_dict()
        audio: Dict[str, float] = {}
        if self.offset is not None:
            audio["offset"] = self.offset
        if self.duration is not None:
            audio["duration"] = self.duration
        if audio:
            result["audio"] = audio
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recipe":
        """Validate and construct a Recipe from dictionary."""
        if not isinstance(data, dict):
            raise ValueError(f"Recipe data must be a dict, got {type(data)}")
        allowed_keys = {"version", "model", "seed", "mask", "audio"}
        unknown = set(data.keys()) - allowed_keys
        if unknown:
            raise ValueError(f"Unknown top-level recipe key(s): {sorted(unknown)}")

        version = data.get("version", 1)
        if not isinstance(version, int) or version != 1:
            raise ValueError(f"Unsupported recipe version: {version}")

        model = data.get("model", "spleeter:2stems")
        if not isinstance(model, str):
            raise ValueError(f"Model descriptor must be a string, got {type(model)}")

        seed_val = data.get("seed")
        if seed_val is not None:
            if isinstance(seed_val, bool) or not isinstance(
                seed_val, (int, np.integer)
            ):
                raise ValueError(
                    f"Recipe seed must be an integer, got {type(seed_val)}"
                )
            seed_val = int(seed_val)

        mask_data = data.get("mask", {})
        mask_cfg = MaskConfig.from_dict(mask_data)

        audio_data = data.get("audio", {})
        if not isinstance(audio_data, dict):
            raise ValueError(f"'audio' must be a dict, got {type(audio_data)}")
        unknown_audio = set(audio_data.keys()) - {"offset", "duration"}
        if unknown_audio:
            raise ValueError(f"Unknown key(s) in 'audio': {sorted(unknown_audio)}")
        offset = audio_data.get("offset")
        if offset is not None:
            if isinstance(offset, bool) or not isinstance(offset, (int, float)):
                raise ValueError(f"'audio.offset' must be numeric, got {offset!r}")
            if offset < 0:
                raise ValueError(f"'audio.offset' must be non-negative, got {offset}")
            offset = float(offset)
        duration = audio_data.get("duration")
        if duration is not None:
            if isinstance(duration, bool) or not isinstance(duration, (int, float)):
                raise ValueError(f"'audio.duration' must be numeric, got {duration!r}")
            if duration <= 0:
                raise ValueError(f"'audio.duration' must be positive, got {duration}")
            duration = float(duration)

        return cls(
            version=version,
            model=model,
            seed=seed_val,
            mask=mask_cfg,
            offset=offset,
            duration=duration,
        )

    def _execute_op(self, mask: np.ndarray, op: MaskOp, op_index: int) -> np.ndarray:
        """Execute a single MaskOp on an input mask array."""
        op_name = op.op
        p = op.params
        if op_name == "contrast":
            return masks.contrast(mask, gamma=float(p["gamma"]))
        if op_name == "gain_bias":
            return masks.gain_bias(
                mask, gain=float(p.get("gain", 1.0)), bias=float(p.get("bias", 0.0))
            )
        if op_name == "threshold":
            return masks.threshold(
                mask,
                threshold=float(p["threshold"]),
                softness=float(p.get("softness", 0.0)),
            )
        if op_name == "quantize":
            return masks.quantize(mask, levels=int(p["levels"]))
        if op_name == "time_shift":
            return masks.time_shift(
                mask, frames=int(p["frames"]), wrap=bool(p.get("wrap", False))
            )
        if op_name == "freq_shift":
            return masks.freq_shift(
                mask, bins=int(p["bins"]), wrap=bool(p.get("wrap", False))
            )
        if op_name == "complement_blend":
            return masks.complement_blend(mask, amount=float(p["amount"]))
        if op_name == "noise":
            seed = (
                op.seed if op.seed is not None else derive_op_seed(self.seed, op_index)
            )
            return masks.noise(mask, amount=float(p["amount"]), seed=seed)
        raise ValueError(f"Unhandled operation: {op_name}")

    def apply_to_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        Apply the recipe operations chain to a single mask array.

        Parameters:
            mask (np.ndarray):
                Input mask array shaped `(frames, bins, channels)`.

        Returns:
            np.ndarray:
                Modified mask array, float32, same shape.
        """
        if not self.mask.enabled or len(self.mask.ops) == 0:
            return mask.copy().astype(np.float32)
        out = mask
        for idx, op in enumerate(self.mask.ops):
            out = self._execute_op(out, op, idx)
        if self.mask.clamp:
            out = np.clip(out, 0.0, 1.0).astype(np.float32)
        return out

    def apply(self, masks_dict: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Apply the recipe operations chain to a dictionary of stem masks.

        Parameters:
            masks_dict (Dict[str, np.ndarray]):
                Mapping of instrument name to mask array.

        Returns:
            Dict[str, np.ndarray]:
                Mapping of instrument name to modified mask array.
        """
        if not self.mask.enabled or len(self.mask.ops) == 0:
            return {
                name: arr.copy().astype(np.float32) for name, arr in masks_dict.items()
            }
        return {name: self.apply_to_mask(arr) for name, arr in masks_dict.items()}

    def clone(self) -> "Recipe":
        """Create a deep copy of this recipe."""
        return copy.deepcopy(self)

    @classmethod
    def load(cls, path: Union[str, PathLike]) -> "Recipe":
        """Load a Recipe from a JSON file."""
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        return cls.from_dict(data)

    def save(self, path: Union[str, PathLike]) -> None:
        """Save recipe to a JSON file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as fp:
            json.dump(self.to_dict(), fp, indent=2)


def load_recipe(path: Union[str, PathLike]) -> Recipe:
    """Load a Recipe from a JSON file."""
    return Recipe.load(path)


def save_recipe(recipe: Recipe, path: Union[str, PathLike]) -> None:
    """Save a Recipe to a JSON file."""
    recipe.save(path)
