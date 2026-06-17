"""One-off runner for demo seed on Windows (SelectorEventLoop)."""
from __future__ import annotations

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.seed.demo_patient import seed

asyncio.run(seed())
