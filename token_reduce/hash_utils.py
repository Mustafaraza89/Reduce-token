from __future__ import annotations

import hashlib
from pathlib import Path


def file_sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 128)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
