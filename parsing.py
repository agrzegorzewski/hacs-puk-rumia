"""Pure parsing utilities for SISMS payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class BinDefinition:
    """Bin metadata provided by the bins endpoint."""

    bin_id: int
    name: str
    waste_type: str
    color: str | None


def parse_iso8601_date(value: str) -> date:
    """Parse an ISO 8601 date or datetime string into a date object."""
    normalized = value.strip()
    if not normalized:
        raise ValueError("Date value is empty")

    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    try:
        return date.fromisoformat(normalized)
    except ValueError:
        try:
            return datetime.fromisoformat(normalized).date()
        except ValueError as err:
            raise ValueError(f"Invalid ISO 8601 date: {value}") from err


def extract_bins(payload: Mapping[str, Any]) -> dict[int, BinDefinition]:
    """Build a dictionary of bins keyed by bin id."""
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("Bins payload does not contain a valid data list")

    bins: dict[int, BinDefinition] = {}
    for item in data:
        if not isinstance(item, Mapping):
            continue

        try:
            bin_id = int(item["id"])
            name = str(item["name"])
        except KeyError, TypeError, ValueError:
            continue

        bins[bin_id] = BinDefinition(
            bin_id=bin_id,
            name=name,
            waste_type=str(item.get("type", "unknown")),
            color=str(item["color"]) if item.get("color") is not None else None,
        )

    return bins


def extract_next_pickups(
    payload: Mapping[str, Any], today: date | None = None
) -> dict[int, date]:
    """Return nearest upcoming reception date for each bin id."""
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("Timetable payload does not contain a valid data list")

    reference = today or date.today()
    next_pickups: dict[int, date] = {}

    for month in data:
        if not isinstance(month, Mapping):
            continue

        receptions = month.get("receptions")
        if not isinstance(receptions, list):
            continue

        for reception in receptions:
            if not isinstance(reception, Mapping):
                continue

            try:
                bin_id = int(reception["binId"])
                pickup_date = parse_iso8601_date(str(reception["date"]))
            except KeyError, TypeError, ValueError:
                continue

            if pickup_date < reference:
                continue

            current = next_pickups.get(bin_id)
            if current is None or pickup_date < current:
                next_pickups[bin_id] = pickup_date

    return next_pickups
