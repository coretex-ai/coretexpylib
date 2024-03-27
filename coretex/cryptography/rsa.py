#     Copyright (C) 2023  Coretex LLC

#     This file is part of Coretex.ai

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Tuple

from Crypto.PublicKey import RSA
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from .random_generator import Random


def _generateRsaNumbers(bits: int, seed: bytes) -> Tuple[int, int, int, int, int]:
    random = Random(seed, hashes.SHA256())
    numbers = RSA.generate(bits, randfunc = random.getRandomBytes, e = 65537)

    return numbers.p, numbers.q, numbers.n, numbers.e, numbers.d


def generateKey(length: int, seed: bytes) -> rsa.RSAPrivateKey:
    # p -> large random prime number
    # q -> large random prime number
    # n -> p * q
    # e -> 65537
    # d -> inverse(e, lcm(p - 1, q - 1))
    p, q, n, e, d = _generateRsaNumbers(length, seed)

    dmp1 = rsa.rsa_crt_dmp1(d, p)
    dmq1 = rsa.rsa_crt_dmq1(d, q)
    iqmp = rsa.rsa_crt_iqmp(p, q)

    privateNumbers = rsa.RSAPrivateNumbers(p, q, d, dmp1, dmq1, iqmp, rsa.RSAPublicNumbers(e, n))
    return privateNumbers.private_key()


def getPrivateKeyBytes(key: rsa.RSAPrivateKey) -> bytes:
    return key.private_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PrivateFormat.PKCS8,
        encryption_algorithm = serialization.NoEncryption()
    )


def getPublicKeyBytes(key: rsa.RSAPublicKey) -> bytes:
    return key.public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.PKCS1
    )


def decrypt(key: rsa.RSAPrivateKey, encryptedData: bytes) -> bytes:
    return key.decrypt(encryptedData, padding = padding.PKCS1v15())
