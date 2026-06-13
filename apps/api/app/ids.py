"""Short, readable, prefixed IDs (e.g. doc_8f1c, clm_001, brf_4d2)."""
from __future__ import annotations

import secrets

_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
_TOKEN_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def _rand(n: int, alphabet: str = _ALPHABET) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(n))


def new_id(prefix: str, n: int = 4) -> str:
    """Generate a prefixed short id, e.g. new_id('doc') -> 'doc_8f1c'."""
    return f"{prefix}_{_rand(n)}"


def new_token(n: int = 10) -> str:
    """Generate an unguessable, URL-safe public token (e.g. for shares)."""
    return _rand(n, _TOKEN_ALPHABET)
