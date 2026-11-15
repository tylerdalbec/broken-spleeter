"""
Deliberate, reproducible abuse of stem-separation models.

Only the model-agnostic NumPy pieces exist so far: mask operations and the
version 1 recipe schema, both carried over from the Broken Spleeter prototype.
See CONCEPT.md and ROADMAP.md at the repository root.
"""

from .recipe import Recipe, load_recipe, save_recipe

__all__ = ["Recipe", "load_recipe", "save_recipe"]
