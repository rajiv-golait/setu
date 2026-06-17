"""Vital sign recording with deterministic out-of-range flags (informational only)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Vital
from app.ids import new_id

FLAG_MESSAGE = "Reading above common reference — share with your doctor"

THRESHOLDS: dict[str, dict] = {
    "blood_pressure": {"systolic_high": 140, "diastolic_high": 90},
    "blood_sugar": {"fasting_high": 126, "fasting_low": 70},
    "spo2": {"percent_low": 94},
    "heart_rate": {"bpm_high": 100, "bpm_low": 50},
}


def flag_vital(vital_type: str, value: dict) -> str | None:
    """Return 'out_of_range' when value crosses common reference thresholds."""
    if vital_type == "blood_pressure":
        systolic = value.get("systolic")
        diastolic = value.get("diastolic")
        if systolic is not None and systolic >= THRESHOLDS["blood_pressure"]["systolic_high"]:
            return "out_of_range"
        if diastolic is not None and diastolic >= THRESHOLDS["blood_pressure"]["diastolic_high"]:
            return "out_of_range"
    elif vital_type == "blood_sugar":
        fasting = value.get("fasting")
        if fasting is not None:
            if fasting > THRESHOLDS["blood_sugar"]["fasting_high"]:
                return "out_of_range"
            if fasting < THRESHOLDS["blood_sugar"]["fasting_low"]:
                return "out_of_range"
    elif vital_type == "spo2":
        percent = value.get("percent")
        if percent is not None and percent < THRESHOLDS["spo2"]["percent_low"]:
            return "out_of_range"
    elif vital_type == "heart_rate":
        bpm = value.get("bpm")
        if bpm is not None:
            if bpm > THRESHOLDS["heart_rate"]["bpm_high"]:
                return "out_of_range"
            if bpm < THRESHOLDS["heart_rate"]["bpm_low"]:
                return "out_of_range"
    return None


async def record(
    db: AsyncSession,
    *,
    patient_id: str,
    vital_type: str,
    value: dict,
    unit: str,
    measured_at: datetime | None,
    recorded_by: str | None,
) -> Vital:
    when = measured_at or datetime.now(timezone.utc)
    flag = flag_vital(vital_type, value)
    row = Vital(
        id=new_id("vit"),
        patient_id=patient_id,
        vital_type=vital_type,
        value=value,
        unit=unit,
        flag=flag,
        recorded_by=recorded_by,
        measured_at=when,
    )
    db.add(row)
    await db.flush()
    return row


async def list_vitals(
    db: AsyncSession,
    patient_id: str,
    vital_type: str | None = None,
) -> list[Vital]:
    stmt = select(Vital).where(Vital.patient_id == patient_id)
    if vital_type is not None:
        stmt = stmt.where(Vital.vital_type == vital_type)
    stmt = stmt.order_by(Vital.measured_at.desc())
    return list((await db.execute(stmt)).scalars().all())


async def series(db: AsyncSession, patient_id: str, vital_type: str) -> list[Vital]:
    return list(
        (
            await db.execute(
                select(Vital)
                .where(Vital.patient_id == patient_id, Vital.vital_type == vital_type)
                .order_by(Vital.measured_at.asc())
            )
        ).scalars().all()
    )


def trend_direction(points: list[Vital]) -> str:
    """Simple up/down/stable from first vs last numeric scalar in value."""
    if len(points) < 2:
        return "stable"

    def _scalar(v: dict) -> float | None:
        for key in ("bpm", "percent", "fasting", "systolic"):
            if key in v and v[key] is not None:
                return float(v[key])
        return None

    first = _scalar(points[0].value)
    last = _scalar(points[-1].value)
    if first is None or last is None:
        return "stable"
    if last > first * 1.05:
        return "up"
    if last < first * 0.95:
        return "down"
    return "stable"
