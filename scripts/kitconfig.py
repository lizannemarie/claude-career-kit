"""Shared helpers for career-kit scripts: the {{PLACEHOLDER}} syntax and config-path lookup.

placeholder_map values are '/'-separated paths into career-kit.config.json, for example
"airtable/fields/fact_interview/Thank-you Sent". Field names may contain spaces and dashes but not '/'.
"""
import re

PH = re.compile(r"\{\{[^{}]+\}\}")


def lookup(cfg, path):
    """Return the value at a '/'-separated path, or raise KeyError(path)."""
    cur = cfg
    for part in path.split("/"):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(path)
        cur = cur[part]
    return cur
