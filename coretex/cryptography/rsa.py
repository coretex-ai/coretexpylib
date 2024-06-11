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
from base64 import b64decode

import os

from Crypto.PublicKey import RSA
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from .random_generator import Random


def _generateRsaNumbers(bits: int, seed: bytes) -> Tuple[int, int, int, int, int]:
    """
        Randomly generates numbers used for calculating RSA public
        and private keys

        Parameters
        ----------
        bits : int
            # of bits in the "n" public number
        seeed : bytes
            Array of bytes which represent seed for generating key in a deterministic way.
            The entropy of the generated key is equal to the entropy of the seed.

        Returns
        Tuple[int, int, int, int, int] -> p, q, n, e, d RSA values, e is always equal to 65537
    """

    random = Random(seed, hashes.SHA256())
    numbers = RSA.generate(bits, randfunc = random.getRandomBytes, e = 65537)

    return numbers.p, numbers.q, numbers.n, numbers.e, numbers.d


def generateKey(length: int, seed: bytes) -> rsa.RSAPrivateKey:
    """
        Generates RSA key-pair with the provided length and seed

        Parameters
        ----------
        length : int
            length of the key-pair
        seed : bytes
            Array of bytes which represent seed for generating key in a deterministic way.
            The entropy of the generated key is equal to the entropy of the seed.

        Returns
        -------
        RSAPrivateKey -> cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey object
    """

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
    """
        Converts the provided key into a byte array.
        Encoding is PEM, Format is PKCS8

        Parameters
        ----------
        key : RSAPrivateKey
            cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey object

        Returns
        -------
        bytes -> RSA private key serialized to bytes
    """

    return key.private_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PrivateFormat.PKCS8,
        encryption_algorithm = serialization.NoEncryption()
    )


def getPublicKeyBytes(key: rsa.RSAPublicKey) -> bytes:
    """
        Converts the provided key into a byte array.
        Encoding is PEM, Format is PKCS1

        Parameters
        ----------
        key : RSAPublicKey
            cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey object

        Returns
        -------
        bytes -> RSA public key serialized to bytes
    """

    return key.public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.PKCS1
    )


def privateKeyFromBytes(keyBytes: bytes) -> rsa.RSAPrivateKey:
    """
        Creates private key object from provided private
        key bytes.

        Parameters
        ----------
        keyBytes : bytes
            private key bytes

        Returns
        -------
        rsa.RSAPrivateKey -> private key object
    """

    key = serialization.load_pem_private_key(keyBytes, password = None)

    if not isinstance(key, rsa.RSAPrivateKey):
        raise TypeError

    return key


def getPrivateKey() -> rsa.RSAPrivateKey:
    """
        Retrieves RSA private key stored in CTX_PRIVATE_KEY
        environment variable in base64 format.

        Returns
        -------
        rsa.RSAPrivateKey -> private key object
    """

    if "CTX_PRIVATE_KEY" not in os.environ:
        raise RuntimeError(f"\"CTX_PRIVATE_KEY\" environment variable not set")

    privateKey = b64decode(os.environ["CTX_PRIVATE_KEY"])
    return privateKeyFromBytes(privateKey)


def decrypt(key: rsa.RSAPrivateKey, value: bytes) -> bytes:
    """
        Decrypts ciphertext encrypted using provided key-pair.
        It is assumed that PKCS#1 padding was used during encryption.

        Parameters
        ----------
        key : rsa.RSAPrivateKey
            private key object
        value : bytes
            ciphertext

        Returns
        -------
        bytes -> decrypted ciphertext
    """

    return key.decrypt(value, padding.PKCS1v15())
