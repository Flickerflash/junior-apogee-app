"""
Utility helpers – logging setup, scoring helpers, and time utilities.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator, Optional

from loguru import logger


# ─── Logger Configuration ────────────────────────────────────────────────────

def setup_logger(level: str = "INFO", log_file: Optional[str] = None) -> None:
    logger.remove()
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, level=level, format=fmt, colorize=True)
    if log_file:
        logger.add(log_file, level=level, rotation="10 MB", retention="14 days", compression="gz")


# ─── Scoring Helpers ─────────────────────────────────────────────────────────

def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return clamp(numerator / denominator)


def score_exact_match(predicted: Any, expected: Any) -> float:
    """Binary exact-match score (1.0 or 0.0)."""
    return 1.0 if predicted == expected else 0.0


def score_string_similarity(predicted: str, expected: str) -> float:
    """Normalised Levenshtein similarity in [0, 1]."""
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    a, b = predicted.lower().strip(), expected.lower().strip()
    if a == b:
        return 1.0
    # Simple character-level overlap
    longer = max(len(a), len(b))
    matches = sum(ca == cb for ca, cb in zip(a, b))
    return clamp(matches / longer)


def score_list_overlap(predicted: list, expected: list) -> float:
    """F1-style overlap between two lists."""
    if not expected:
        return 1.0 if not predicted else 0.0
    pred_set = set(str(p).lower() for p in predicted)
    exp_set  = set(str(e).lower() for e in expected)
    if not pred_set:
        return 0.0
    precision = len(pred_set & exp_set) / len(pred_set)
    recall    = len(pred_set & exp_set) / len(exp_set)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def deterministic_hash(obj: Any) -> str:
    """Stable SHA-256 hash of any JSON-serialisable object."""
    raw = json.dumps(obj, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


# ─── Timing Utilities ────────────────────────────────────────────────────────

@contextmanager
def timer(label: str = "") -> Generator[dict, None, None]:
    """Context manager that records elapsed time (ms) into the yielded dict."""
    result: dict = {"elapsed_ms": 0.0}
    t0 = time.perf_counter()
    try:
        yield result
    finally:
        result["elapsed_ms"] = (time.perf_counter() - t0) * 1000
        if label:
            logger.debug(f"{label} completed in {result['elapsed_ms']:.1f} ms")


def utcnow_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


# ─── Pretty Printers ─────────────────────────────────────────────────────────

def format_score(score: float) -> str:
    return f"{score * 100:.1f}%"


def format_latency(ms: float) -> str:
    if ms >= 1000:
        return f"{ms / 1000:.2f}s"
    return f"{ms:.0f}ms"


def format_cost(usd: float) -> str:
    if usd < 0.001:
        return f"${usd * 100:.4f}¢"
    return f"${usd:.4f}"
