#!/usr/bin/env python
# coding: utf8

"""
Broken Spleeter — deliberate, reproducible corruption of Spleeter inference.

This package wraps ordinary Spleeter inference rather than editing it.
Everything here is an intervention applied to the normal signal path, and
every intervention is bypassable: with no corruption configured, output is
bit-identical to unmodified Spleeter.
"""

from .recipe import Recipe, load_recipe, save_recipe
from .separator import BrokenSeparator

__all__ = ["BrokenSeparator", "Recipe", "load_recipe", "save_recipe"]
