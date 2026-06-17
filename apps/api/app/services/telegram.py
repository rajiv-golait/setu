"""Telegram bot service — the primary interface.

Flow (handle_update routes a Telegram Update):
  /start                -> create/find patient by chat_id, send greeting
  photo / document      -> download, store, kick the pipeline (reply when done)
  "summary" / "सारांश"  -> reply with the tokenized brief link
  any other text        -> usage hint

HTTP client: httpx.AsyncClient against https://api.telegram.org/bot{TOKEN}/.
File download: https://api.telegram.org/file/bot{TOKEN}/{file_path}.

The webhook router always returns 200 and schedules handle_update in the
background, so a slow/failed handler never causes Telegram to retry.
"""
from __future__ import annotations

import hashlib
import logging
import os

import httpx
from sqlalchemy import select

from app import jobs_store
from app.config import settings
from app.db.models import Document, Patient
from app.db.session import SessionLocal
from app.ids import new_id, new_token
from app.seed.fixtures import BRIEF_HANDOFF_MSG
from app.services import persistence

logger = logging.getLogger("setu.telegram")

GREETING = (
    "नमस्कार! कोणतेही प्रिस्क्रिप्शन किंवा लॅब रिपोर्टचा फोटो पाठवा "
    "— मी मराठीत समजावून सांगेन."
)
READING = "📋 वाचत आहे... एक मिनिट थांबा."
NO_REPORT = "अजून कोणताही रिपोर्ट नाही. एक फोटो पाठवा."
USAGE = "फोटो पाठवा किंवा 'summary' लिहा."

_SUMMARY_WORDS = {"summary", "सारांश"}
_EXT_BY_MIME = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}


# --- Telegram HTTP client ------------------------------------------------- #
def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"


def _file_url(file_path: str) -> str:
    return f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"


async def send_message(chat_id: str | int, text: str, parse_mode: str = "Markdown") -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.info("[telegram dry-run] -> %s: %s", chat_id, text)
        return
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _api_url("sendMessage"),
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
        )
        if resp.status_code != 200:
            logger.warning("sendMessage failed %s: %s", resp.status_code, resp.text)


async def send_document(chat_id: str | int, document_url: str, caption: str | None = None) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.info("[telegram dry-run] doc -> %s: %s", chat_id, document_url)
        return
    payload = {"chat_id": chat_id, "document": document_url}
    if caption:
        payload["caption"] = caption
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(_api_url("sendDocument"), json=payload)
        if resp.status_code != 200:
            logger.warning("sendDocument failed %s: %s", resp.status_code, resp.text)


async def _get_file_path(file_id: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(_api_url("getFile"), params={"file_id": file_id})
        resp.raise_for_status()
        return resp.json()["result"]["file_path"]


async def _download(file_path: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(_file_url(file_path))
        resp.raise_for_status()
        return resp.content


# --- Update routing ------------------------------------------------------- #
async def handle_update(update: dict) -> None:
    """Route a Telegram Update to the right handler. Never raises."""
    try:
        message = update.get("message") or update.get("edited_message")
        if not message:
            logger.info("telegram update with no message: keys=%s", sorted(update.keys()))
            return

        chat_id = str(message["chat"]["id"])
        text = (message.get("text") or "").strip()

        if text.startswith("/start"):
            await _handle_start(chat_id)
            return

        if "photo" in message or "document" in message:
            await _handle_media(chat_id, message)
            return

        if text.lower() in _SUMMARY_WORDS:
            await _handle_summary(chat_id)
            return

        await send_message(chat_id, USAGE)
    except Exception as exc:  # noqa: BLE001 — webhook handler must never blow up
        logger.exception("handle_update failed: %s", exc)


async def _get_or_create_patient(db, chat_id: str) -> Patient:
    patient = (
        await db.execute(select(Patient).where(Patient.telegram_chat_id == chat_id))
    ).scalar_one_or_none()
    if patient is None:
        patient = Patient(
            id=new_id("pat"),
            display_name=None,
            lang_pref="mr",
            telegram_chat_id=chat_id,
            patient_token=new_token(10),
        )
        db.add(patient)
        await db.flush()
    return patient


async def _handle_start(chat_id: str) -> None:
    async with SessionLocal() as db:
        await _get_or_create_patient(db, chat_id)
        await db.commit()
    await send_message(chat_id, GREETING)


async def _handle_media(chat_id: str, message: dict) -> None:
    # Resolve the largest photo or the document's file_id + mime.
    file_id, mime = _extract_file(message)
    if not file_id:
        await send_message(chat_id, USAGE)
        return

    await send_message(chat_id, READING)

    try:
        tg_path = await _get_file_path(file_id)
        data = await _download(tg_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("telegram file download failed: %s", exc)
        await send_message(chat_id, "फाइल डाउनलोड करता आली नाही. पुन्हा प्रयत्न करा.")
        return

    async with SessionLocal() as db:
        patient = await _get_or_create_patient(db, chat_id)
        patient_id = patient.id

        # Store using the existing convention: STORAGE_PATH/{doc_id}{ext}.
        os.makedirs(settings.STORAGE_PATH, exist_ok=True)
        doc_id = new_id("doc")
        ext = _EXT_BY_MIME.get(mime, ".jpg")
        storage_path = os.path.join(settings.STORAGE_PATH, f"{doc_id}{ext}")
        with open(storage_path, "wb") as f:
            f.write(data)

        doc = Document(
            id=doc_id,
            patient_id=patient_id,
            doc_type=None,
            storage_path=storage_path,
            mime=mime,
            source="telegram",
            status="pending",
            original_hash=hashlib.sha256(data).hexdigest(),
        )
        db.add(doc)
        await db.commit()

    job_id = new_id("job")
    state = jobs_store.new_job_state(job_id, doc_id, patient_id)
    await jobs_store.save(state)

    # Run the pipeline; it sends the explanation + brief link to this chat.
    # Imported here to avoid a circular import (orchestrator imports telegram).
    from app.services.orchestrator import run_pipeline

    await run_pipeline(job_id, doc_id, patient_id, reply_chat_id=chat_id)


def _extract_file(message: dict) -> tuple[str | None, str]:
    if "photo" in message and message["photo"]:
        # Telegram sends multiple sizes; the last is the largest.
        return message["photo"][-1]["file_id"], "image/jpeg"
    if "document" in message:
        doc = message["document"]
        return doc.get("file_id"), doc.get("mime_type", "application/octet-stream")
    return None, ""


async def _handle_summary(chat_id: str) -> None:
    async with SessionLocal() as db:
        patient = (
            await db.execute(select(Patient).where(Patient.telegram_chat_id == chat_id))
        ).scalar_one_or_none()
        if patient is None:
            await send_message(chat_id, NO_REPORT)
            return
        brief = await persistence.latest_brief(db, patient.id)
        if brief is None:
            await send_message(chat_id, NO_REPORT)
            return
        # Find this patient's most recent share token for the brief link.
        from app.db.models import Share

        share = (
            await db.execute(
                select(Share)
                .where(Share.patient_id == patient.id)
                .order_by(Share.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        token = share.token if share else patient.patient_token

    brief_url = f"{settings.BRIEF_BASE_URL.rstrip('/')}/brief/{token}"
    await send_message(chat_id, BRIEF_HANDOFF_MSG.format(url=brief_url))
