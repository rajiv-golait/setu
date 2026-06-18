#!/usr/bin/env python3
"""Generate VAPID keys for Web Push (medicine reminders).

Usage:
  cd apps/api && python scripts/generate_vapid.py

Add the printed lines to apps/api/.env and restart the API.

Note: if you already have keys, skip this — just set VAPID_* in .env.
"""
from __future__ import annotations

import base64

from cryptography.hazmat.primitives.asymmetric import ec


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def main() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_bytes = private_key.private_numbers().private_value.to_bytes(32, "big")
    pub = private_key.public_key().public_numbers()
    public_bytes = b"\x04" + pub.x.to_bytes(32, "big") + pub.y.to_bytes(32, "big")

    print("Add to apps/api/.env:")
    print(f"VAPID_PUBLIC_KEY={_b64url(public_bytes)}")
    print(f"VAPID_PRIVATE_KEY={_b64url(private_bytes)}")
    print("VAPID_CONTACT_EMAIL=noreply@setu.health")


if __name__ == "__main__":
    main()
