import base64
import hashlib


MAX_NAME_LENGTH = 50


def hashCacheName(name: str, suffix: str) -> str:
    if MAX_NAME_LENGTH - len(name) < 8:
        raise ValueError(">> [Coretex] Failed to cache dataset. Dataset name too long")

    suffixByteHash = hashlib.md5(suffix.encode()).digest()
    suffixHash = base64.b64encode(suffixByteHash)
    cacheName = name + "_" + suffixHash.decode("ascii")

    return cacheName[:MAX_NAME_LENGTH] if len(cacheName) > MAX_NAME_LENGTH else cacheName
