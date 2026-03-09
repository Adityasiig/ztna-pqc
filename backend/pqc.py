"""
PQC utilities. Attempts to use the pqcrypto Kyber512 library.
Falls back to a secure random simulation if the library is not installed,
so the application always starts correctly even without pqcrypto.
"""

try:
    from pqcrypto.kem.kyber512 import generate_keypair as _kyber_gen
    USE_REAL_PQC = True
except ImportError:
    USE_REAL_PQC = False

import os

def generate_keypair():
    """
    Generate a Kyber512 keypair (or a simulated 800-byte random key pair).

    Returns:
        tuple[bytes, bytes]: (public_key, private_key)
    """
    if USE_REAL_PQC:
        public_key, private_key = _kyber_gen()
        return public_key, private_key
    else:
        # Secure-random simulation: Kyber512 public key is 800 bytes
        public_key = os.urandom(800)
        private_key = os.urandom(1632)
        return public_key, private_key
