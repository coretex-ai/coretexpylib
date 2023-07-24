import base64
import hashlib


maxNameLength = 50


def md5(object: bytes) -> bytes:
    return hashlib.md5(object).digest()


def hashCacheName(name: str, suffix: str) -> str:
    suffixHash = base64.b64encode(md5(suffix.encode()))
    cacheName = name + "_" + suffixHash.decode("ascii")

    return cacheName[:maxNameLength] if len(cacheName) > maxNameLength else cacheName
