"""
Cryptographically secure activation code generator for INFINITY Tweaker.
Format: INF-XXXX-XXXX-XXXX (Alphanumeric uppercase, omitting ambiguous characters like 0/O, 1/I)
"""
import secrets
import string

SAFE_CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

def generate_activation_code(prefix: str = "INF") -> str:
    """Generate an unpredictable, high-entropy 12-char formatted activation code."""
    part1 = "".join(secrets.choice(SAFE_CHARS) for _ in range(4))
    part2 = "".join(secrets.choice(SAFE_CHARS) for _ in range(4))
    part3 = "".join(secrets.choice(SAFE_CHARS) for _ in range(4))
    return f"{prefix}-{part1}-{part2}-{part3}"
