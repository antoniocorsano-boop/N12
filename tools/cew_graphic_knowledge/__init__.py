"""CEW system-level graphic convention knowledge fabric.

Compatibility policy for the pattern-aware v2 resolver:
- if either side lacks a usable graphic-pattern signature, fall back to context-only affinity;
- when both pattern and context are available, pattern similarity may reduce transfer but
  must never rescue an unrelated project context.

The policy is applied at package import so every CEW consumer of ``fabric`` receives the
same conservative resolver semantics while legacy knowledge packs remain usable.
"""

from . import fabric as fabric

_NATIVE_PATTERN_AFFINITY = fabric.pattern_affinity


def _compatible_pattern_affinity(target, source):
    target_pattern = fabric.pattern_core(target)
    source_pattern = fabric.pattern_core(source)
    if not target_pattern:
        return {
            "score": 1.0,
            "matched": [],
            "mismatched": [],
            "missing": [],
            "mode": "UNSPECIFIED_TARGET_CONTEXT_ONLY",
        }
    if not source_pattern:
        return {
            "score": 1.0,
            "matched": [],
            "mismatched": [],
            "missing": sorted(target_pattern),
            "mode": "UNSPECIFIED_SOURCE_CONTEXT_ONLY",
        }
    return _NATIVE_PATTERN_AFFINITY(target, source)


def _conservative_combined_affinity(context_score: float, pattern_score: float) -> float:
    if context_score <= 0 or pattern_score <= 0:
        return 0.0
    return round(context_score * pattern_score, 6)


fabric.pattern_affinity = _compatible_pattern_affinity
fabric.combined_affinity = _conservative_combined_affinity
