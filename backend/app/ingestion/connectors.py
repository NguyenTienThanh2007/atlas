"""Connectors fetch raw bytes and nothing else: no parsing, no business rules.

Only local files are supported. Network providers need credentials and a confirmed licence
(see data/SOURCES.md) and are intentionally not implemented.
"""

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


class InputError(Exception):
    """The input cannot be read or parsed at all; the whole run fails."""


@dataclass(frozen=True)
class RawInput:
    ref: str
    content: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


def read_local_file(path: Path) -> RawInput:
    try:
        return RawInput(ref=f"file://{path.resolve()}", content=path.read_bytes())
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc.strerror}") from exc


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [k for k, _ in pairs]
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    if dupes:
        raise InputError(f"duplicate JSON keys: {', '.join(dupes)}")
    return dict(pairs)


def parse_json(raw: RawInput) -> Any:
    """Parse JSON with numbers as exact Decimals (never floats) and no duplicate keys."""
    try:
        return json.loads(
            raw.content.decode("utf-8"),
            parse_float=Decimal,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except UnicodeDecodeError as exc:
        raise InputError(f"{raw.ref} is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"{raw.ref} is not valid JSON: {exc.msg} at line {exc.lineno}") from exc
