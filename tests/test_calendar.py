"""Minimal tests for PUK Rumia calendar entity behavior."""

from __future__ import annotations

from datetime import date, datetime
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from parsing import BinDefinition

_CALENDAR_MODULE_PATH = Path(__file__).resolve().parents[1] / "calendar.py"
_CALENDAR_SPEC = importlib.util.spec_from_file_location(
    "puk_rumia_calendar", _CALENDAR_MODULE_PATH
)
if _CALENDAR_SPEC is None or _CALENDAR_SPEC.loader is None:
    raise ImportError("Unable to import calendar platform module")
_CALENDAR_MODULE = importlib.util.module_from_spec(_CALENDAR_SPEC)
_CALENDAR_SPEC.loader.exec_module(_CALENDAR_MODULE)
PukRumiaPickupCalendar = _CALENDAR_MODULE.PukRumiaPickupCalendar


class TestCalendarMinimal(unittest.IsolatedAsyncioTestCase):
    """Check next event and range filtering for calendar entities."""

    async def test_calendar_exposes_next_pickup_event(self) -> None:
        """Event should point at the next pickup date."""
        bin_definition = BinDefinition(
            bin_id=309,
            name="Zmieszane odpady komunalne",
            waste_type="BLACK",
            color="#2a2e34",
        )
        coordinator = MagicMock()
        coordinator.data = SimpleNamespace(
            bins={309: bin_definition},
            pickup_dates={309: [date(2026, 7, 21), date(2026, 8, 4)]},
        )
        coordinator.last_update_success = True
        coordinator.async_add_listener = MagicMock(return_value=lambda: None)

        entity = PukRumiaPickupCalendar(coordinator, "entry-1", bin_definition)

        assert entity.event is not None
        self.assertEqual(entity.event.start, date(2026, 7, 21))

        events = await entity.async_get_events(
            MagicMock(),
            datetime(2026, 7, 1, 0, 0, 0),
            datetime(2026, 8, 1, 0, 0, 0),
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].start, date(2026, 7, 21))
