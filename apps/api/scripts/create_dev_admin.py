#!/usr/bin/env python3
"""Create or update the dev admin account (email + password).

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in apps/api/.env.

Usage:
  cd apps/api
  python scripts/create_dev_admin.py

Optional env overrides:
  DEV_ADMIN_EMAIL=itsmerajiv021@gmail.com
  DEV_ADMIN_PASSWORD=setu-admin-dev
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import supabase_admin


async def main() -> None:
    email = os.getenv("DEV_ADMIN_EMAIL", "itsmerajiv021@gmail.com")
    password = os.getenv("DEV_ADMIN_PASSWORD", "setu-admin-dev")
    user_id = await supabase_admin.ensure_email_admin(email, password)
    print("Admin ready.")
    print(f"  Email:    {email}")
    print(f"  Password: {password}")
    print(f"  User id:  {user_id}")
    print("Sign in at http://localhost:3000/admin/login")


if __name__ == "__main__":
    asyncio.run(main())
