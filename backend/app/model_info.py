"""Model fingerprinting: sha256 digest of the model weights file."""

import hashlib
import os

_FINGERPRINT_CACHE: dict[str, str] = {}

_CHUNK_BYTES = 1024 * 1024  # 1 MiB


def model_fingerprint(path) -> str | None:
    """Return the hex sha256 of the file at ``path``, or None if it is missing.

    Successful digests are cached per path so the file is hashed only once.
    """
    if path in _FINGERPRINT_CACHE:
        return _FINGERPRINT_CACHE[path]

    if not os.path.isfile(path):
        return None

    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)

    hexdigest = digest.hexdigest()
    _FINGERPRINT_CACHE[path] = hexdigest
    return hexdigest
