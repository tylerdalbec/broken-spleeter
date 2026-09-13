#!/usr/bin/env python
# coding: utf8

"""
Command-line interface for Broken Spleeter.

Provides subcommands for rendering recipes, sweeping parameter variations,
and verifying baseline bypass determinism:

    python -m broken render INPUT --recipe R.json -o DIR
    python -m broken sweep INPUT --op OP --param NAME --values V1,V2,... -o DIR
    python -m broken verify-bypass INPUT
"""

import argparse
import hashlib
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# pyright: reportMissingImports=false
# pylint: disable=import-error
import numpy as np

from spleeter.audio import Codec

from .recipe import OP_SPECS, MaskConfig, MaskOp, Recipe, load_recipe
from .separator import BrokenSeparator

# pylint: enable=import-error


REFERENCE_HASHES_2STEMS: Dict[str, str] = {
    "vocals.wav": ("a4ceacf9e24656693d344dd0231b3ade323ab2be5256bffd65c5c0472bff30a3"),
    "accompaniment.wav": (
        "a3fd23625abe7003926255d65261c0a54acdb0cbd97f2efc597d8a67626a79f1"
    ),
}

DEFAULT_OFFSET = 0.0
DEFAULT_DURATION = 600.0


def sanitize_filename(name: str) -> str:
    """Sanitize string for safe usage in Windows filesystem paths."""
    # Replace illegal Windows characters: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
    # Strip trailing spaces or dots which Windows disallows
    sanitized = sanitized.rstrip(" .")
    return sanitized or "unnamed"


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as fp:
        while chunk := fp.read(65536):
            h.update(chunk)
    return h.hexdigest()


def op_param_types(op_name: str) -> Dict[str, Any]:
    """Parameter types an operation accepts, including `seed` if it is seeded."""
    spec = OP_SPECS[op_name]
    types = dict(spec["types"])
    if spec.get("seeded"):
        types["seed"] = (int, np.integer)
    return types


def parse_param_value(op_name: str, param_name: str, raw: str) -> Any:
    """
    Parse a command-line string into the type an operation parameter expects.

    Booleans accept only `true` or `false`, so a typo cannot silently become
    `False`.

    Raises:
        ValueError:
            If the parameter is unknown for the operation, or the string does
            not parse as the parameter's type.
    """
    types = op_param_types(op_name)
    if param_name not in types:
        raise ValueError(
            f"unknown param '{param_name}' for op '{op_name}'. "
            f"Allowed: {sorted(types)}"
        )
    expected_type = types[param_name]
    text = raw.strip()
    if expected_type is bool:
        if text.lower() not in ("true", "false"):
            raise ValueError(
                f"param '{param_name}' for op '{op_name}' must be true or false, "
                f"got '{raw}'"
            )
        return text.lower() == "true"
    try:
        if expected_type == (int, np.integer):
            return int(text)
        return float(text)
    except ValueError:
        raise ValueError(
            f"invalid value '{raw}' for param '{param_name}' of op '{op_name}'"
        ) from None


def parse_fixed_params(
    op_name: str, assignments: Optional[List[str]]
) -> Dict[str, Any]:
    """
    Parse repeated `--set NAME=VALUE` arguments for the swept operation.

    Raises:
        ValueError:
            If an assignment is malformed, repeated, or names an unknown
            parameter.
    """
    fixed: Dict[str, Any] = {}
    for item in assignments or []:
        name, separator, raw = item.partition("=")
        name = name.strip()
        if not separator or not name:
            raise ValueError(f"--set expects NAME=VALUE, got '{item}'")
        if name in fixed:
            raise ValueError(f"--set gives '{name}' more than once")
        fixed[name] = parse_param_value(op_name, name, raw)
    return fixed


def variation_label(
    op_name: str, param_name: str, value: Any, requested_ms: Optional[float] = None
) -> str:
    """
    Label identifying one sweep variation.

    Millisecond sweeps carry the requested value as well as the resolved frame
    count, because several requested values can round to the same frame.
    """
    label = f"{op_name}.{param_name}={value}"
    if requested_ms is not None:
        label += f"_{requested_ms:g}ms"
    return label


def resolve_audio_window(
    args: argparse.Namespace, recipe: Optional[Recipe]
) -> Tuple[float, float]:
    """
    Resolve the excerpt to load: explicit flags, then the recipe, then defaults.
    """
    offset = args.offset
    if offset is None:
        offset = recipe.offset if recipe is not None else None
    duration = args.duration
    if duration is None:
        duration = recipe.duration if recipe is not None else None
    return (
        DEFAULT_OFFSET if offset is None else offset,
        DEFAULT_DURATION if duration is None else duration,
    )


def handle_render(args: argparse.Namespace) -> int:
    """Execute the 'render' subcommand."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    recipe_path = Path(args.recipe)
    if not recipe_path.exists():
        print(f"Error: recipe file not found: {recipe_path}", file=sys.stderr)
        return 1

    try:
        recipe = load_recipe(recipe_path)
    except Exception as exc:
        print(f"Error parsing recipe: {exc}", file=sys.stderr)
        return 1

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    offset, duration = resolve_audio_window(args, recipe)

    print(f"Loading audio '{input_path}' (offset {offset} s, duration {duration} s)...")
    start_time = time.time()
    with BrokenSeparator(recipe.model) as sep:
        waveform = sep.load_audio(str(input_path), offset=offset, duration=duration)
        if recipe.is_bypass:
            print("Recipe mask stage disabled or empty: using structural bypass.")
            sources = sep.separate(waveform, str(input_path))
        else:
            print("Estimating masks...")
            masks = sep.estimate_masks(waveform, str(input_path))
            print("Applying recipe mask operations...")
            corrupted = recipe.apply(masks)
            print("Separating with corrupted masks...")
            sources = sep.separate(waveform, str(input_path), masks=corrupted)

        print(f"Saving output to '{output_dir}'...")
        sep.save_to_file(
            sources,
            str(input_path),
            str(output_dir),
            filename_format="{filename}/{instrument}.{codec}",
            codec=Codec.WAV,
        )

    elapsed = time.time() - start_time
    print(f"Render completed in {elapsed:.2f} s.")
    return 0


def handle_sweep(args: argparse.Namespace) -> int:
    """Execute the 'sweep' subcommand."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    op_name = args.op
    if op_name not in OP_SPECS:
        print(
            f"Error: unknown op '{op_name}'. Allowed: {sorted(OP_SPECS.keys())}",
            file=sys.stderr,
        )
        return 1

    param_name = args.param
    allowed_params = op_param_types(op_name)
    if param_name not in allowed_params:
        print(
            f"Error: unknown param '{param_name}' for op '{op_name}'. "
            f"Allowed: {sorted(allowed_params)}",
            file=sys.stderr,
        )
        return 1

    try:
        fixed_params = parse_fixed_params(op_name, args.set)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if param_name in fixed_params:
        print(
            f"Error: '{param_name}' is both swept and fixed with --set",
            file=sys.stderr,
        )
        return 1

    base_recipe: Optional[Recipe] = None
    if args.recipe:
        recipe_path = Path(args.recipe)
        if not recipe_path.exists():
            print(f"Error: base recipe not found: {recipe_path}", file=sys.stderr)
            return 1
        try:
            base_recipe = load_recipe(recipe_path)
        except Exception as exc:
            print(f"Error loading base recipe: {exc}", file=sys.stderr)
            return 1
        if not base_recipe.mask.enabled:
            print(
                "Error: base recipe has mask.enabled false, so the swept operation "
                "would never run. Enable the mask stage in the base recipe.",
                file=sys.stderr,
            )
            return 1

    model_name = base_recipe.model if base_recipe is not None else "spleeter:2stems"
    unit = args.unit

    if unit is not None:
        if unit.lower() != "ms":
            print(
                f"Error: unsupported unit '{unit}'. Supported: 'ms'",
                file=sys.stderr,
            )
            return 1
        if op_name != "time_shift" or param_name != "frames":
            print(
                "Error: --unit ms is only valid for op 'time_shift' with "
                f"param 'frames', got '{op_name}.{param_name}'",
                file=sys.stderr,
            )
            return 1

    raw_values = [v.strip() for v in args.values.split(",") if v.strip()]
    if not raw_values:
        print("Error: --values must contain at least one value", file=sys.stderr)
        return 1

    with BrokenSeparator(model_name) as sep:
        resolved_values: List[Any] = []
        labels: List[str] = []

        if unit is not None:
            sample_rate = sep.sample_rate
            frame_step = sep._params["frame_step"]
            ms_per_frame = (frame_step / sample_rate) * 1000.0

            requested_ms: List[float] = []
            for v in raw_values:
                try:
                    requested_ms.append(float(v))
                except ValueError:
                    print(
                        f"Error: invalid numeric value for ms: '{v}'",
                        file=sys.stderr,
                    )
                    return 1

            frame_buckets: Dict[int, List[float]] = {}
            for req_ms in requested_ms:
                calc_frames = int(round(req_ms / ms_per_frame))
                frame_buckets.setdefault(calc_frames, []).append(req_ms)
                resolved_values.append(calc_frames)
                labels.append(variation_label(op_name, param_name, calc_frames, req_ms))

            for f_val, req_list in frame_buckets.items():
                if len(req_list) > 1:
                    joined = ", ".join(f"{v:g} ms" for v in req_list)
                    print(
                        f"Warning: multiple requested values ({joined}) "
                        f"resolve to the same frame count: {f_val} frames",
                        file=sys.stderr,
                    )
        else:
            for v in raw_values:
                try:
                    parsed_val = parse_param_value(op_name, param_name, v)
                except ValueError as exc:
                    print(f"Error: {exc}", file=sys.stderr)
                    return 1
                resolved_values.append(parsed_val)
                labels.append(variation_label(op_name, param_name, parsed_val))

        duplicates = sorted({label for label in labels if labels.count(label) > 1})
        if duplicates:
            print(
                f"Error: values produce duplicate variations {duplicates}; "
                "each would overwrite the other's output",
                file=sys.stderr,
            )
            return 1

        # Validate every operation before any audio work, so a bad --set or
        # value fails immediately instead of partway through the sweep.
        op_objects: List[MaskOp] = []
        for val, label in zip(resolved_values, labels):
            op_dict: Dict[str, Any] = {"op": op_name, **fixed_params, param_name: val}
            try:
                op_objects.append(MaskOp.from_dict(op_dict))
            except ValueError as exc:
                print(
                    f"Error creating op for variation '{label}': {exc}",
                    file=sys.stderr,
                )
                return 1

        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        input_stem = input_path.stem
        offset, duration = resolve_audio_window(args, base_recipe)

        print(
            f"Loading audio '{input_path}' "
            f"(offset {offset} s, duration {duration} s)..."
        )
        waveform = sep.load_audio(str(input_path), offset=offset, duration=duration)

        print("Running initial mask estimation (analyzing once for all variations)...")
        est_start = time.time()
        estimated_masks = sep.estimate_masks(waveform, str(input_path))
        est_elapsed = time.time() - est_start
        print(f"Base mask estimation completed in {est_elapsed:.2f} s.")

        print(f"Executing sweep over {len(op_objects)} variation(s)...")
        for idx, (op_obj, label) in enumerate(zip(op_objects, labels), start=1):
            var_start = time.time()

            if base_recipe is not None:
                var_recipe = base_recipe.clone()
            else:
                var_recipe = Recipe(
                    model=model_name,
                    seed=0,
                    mask=MaskConfig(enabled=True, clamp=False, ops=[]),
                )
            var_recipe.offset = offset
            var_recipe.duration = duration
            var_recipe.mask.ops.append(op_obj)

            corrupted_masks = var_recipe.apply(estimated_masks)
            sources = sep.separate(waveform, str(input_path), masks=corrupted_masks)

            safe_label = sanitize_filename(label)
            target_var_dir = output_dir / input_stem / safe_label
            target_var_dir.mkdir(parents=True, exist_ok=True)

            sep.save_to_file(
                sources,
                str(input_path),
                str(target_var_dir),
                filename_format="{instrument}.{codec}",
                codec=Codec.WAV,
            )
            var_recipe.save(target_var_dir / "recipe.json")

            var_elapsed = time.time() - var_start
            print(
                f"[{idx}/{len(op_objects)}] Rendered '{label}' "
                f"in {var_elapsed:.2f} s -> {target_var_dir}"
            )

    print("Sweep complete.")
    return 0


def handle_verify_bypass(args: argparse.Namespace) -> int:
    """Execute the 'verify-bypass' subcommand."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    print(f"Running structural bypass render for '{input_path}'...")
    with BrokenSeparator("spleeter:2stems") as sep:
        waveform = sep.load_audio(str(input_path))
        # Structural bypass: separate without mask arguments
        sources = sep.separate(waveform, str(input_path))

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            sep.save_to_file(
                sources,
                str(input_path),
                str(tmp_path),
                filename_format="{instrument}.{codec}",
                codec=Codec.WAV,
            )

            wav_files = sorted(tmp_path.glob("*.wav"))
            if not wav_files:
                print("Error: no WAV stems were generated", file=sys.stderr)
                return 1

            print("\nBypass Render Stem Checksums (SHA-256):")
            print("=" * 72)

            all_matched = True
            for wav in wav_files:
                stem_name = wav.name
                calc_hash = compute_file_sha256(wav)
                ref_hash = REFERENCE_HASHES_2STEMS.get(stem_name)

                print(f"Stem: {stem_name}")
                print(f"  Calculated SHA-256: {calc_hash}")
                if ref_hash is not None:
                    print(f"  Reference SHA-256:  {ref_hash}")
                    if calc_hash == ref_hash:
                        print("  Status: MATCH")
                    else:
                        print("  Status: MISMATCH")
                        all_matched = False
                else:
                    print("  Reference SHA-256:  (none recorded for this stem)")
                print("-" * 72)

            if input_path.name == "audio_example.mp3":
                if all_matched:
                    print("Verification successful: output matches recorded baseline.")
                else:
                    print(
                        "Verification note: output differed from recorded baseline. "
                        "See ENVIRONMENT.md §3.4 for expected variations across "
                        "environments."
                    )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="python -m broken",
        description="Broken Spleeter — mask manipulation and failure sound design.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: render
    parser_render = subparsers.add_parser(
        "render", help="Render audio using a recipe JSON file."
    )
    parser_render.add_argument("input", help="Path to input audio file.")
    parser_render.add_argument(
        "--recipe", required=True, help="Path to recipe JSON file."
    )
    parser_render.add_argument(
        "-o", "--output", required=True, help="Output destination directory."
    )
    parser_render.add_argument(
        "--offset",
        type=float,
        default=None,
        help="Audio start offset in seconds (default: recipe value, else 0.0).",
    )
    parser_render.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Audio duration in seconds (default: recipe value, else 600.0).",
    )
    parser_render.set_defaults(func=handle_render)

    # Subcommand: sweep
    parser_sweep = subparsers.add_parser(
        "sweep", help="Sweep a parameter value across multiple renders."
    )
    parser_sweep.add_argument("input", help="Path to input audio file.")
    parser_sweep.add_argument(
        "--op", required=True, help="Mask operation name (e.g. time_shift, quantize)."
    )
    parser_sweep.add_argument(
        "--param", required=True, help="Parameter name to sweep (e.g. frames, levels)."
    )
    parser_sweep.add_argument(
        "--values",
        required=True,
        help="Comma-separated list of values (e.g. '-4,0,4' or '0,10,25').",
    )
    parser_sweep.add_argument(
        "-o", "--output", required=True, help="Output destination directory."
    )
    parser_sweep.add_argument(
        "--set",
        action="append",
        metavar="NAME=VALUE",
        help=(
            "(Optional, repeatable) Hold another parameter of the swept op fixed, "
            "e.g. --set wrap=true."
        ),
    )
    parser_sweep.add_argument(
        "--recipe",
        default=None,
        help="(Optional) Base recipe JSON file to append swept op to.",
    )
    parser_sweep.add_argument(
        "--unit",
        default=None,
        help="(Optional) Unit for swept values ('ms' for time_shift frames).",
    )
    parser_sweep.add_argument(
        "--offset",
        type=float,
        default=None,
        help="Audio start offset in seconds (default: base recipe value, else 0.0).",
    )
    parser_sweep.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Audio duration in seconds (default: base recipe value, else 600.0).",
    )
    parser_sweep.set_defaults(func=handle_sweep)

    # Subcommand: verify-bypass
    parser_verify = subparsers.add_parser(
        "verify-bypass",
        help="Render using structural bypass and display stem checksums.",
    )
    parser_verify.add_argument("input", help="Path to input audio file.")
    parser_verify.set_defaults(func=handle_verify_bypass)

    if argv is None:
        argv = sys.argv[1:]
    processed_argv: List[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--values" and i + 1 < len(argv):
            val = argv[i + 1]
            if val.startswith("-") and not val.startswith("--"):
                processed_argv.append(f"--values={val}")
                i += 2
                continue
        processed_argv.append(arg)
        i += 1

    parsed = parser.parse_args(processed_argv)
    return parsed.func(parsed)


if __name__ == "__main__":
    sys.exit(main())
