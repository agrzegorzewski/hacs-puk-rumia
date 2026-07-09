"""Minimal integration-level tests for config flow and sensor entity."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock

from config_flow import PukRumiaConfigFlow
from const import CONF_UNIT_ID
from parsing import BinDefinition
from sensor import PukRumiaPickupSensor


class TestIntegrationMinimal(unittest.IsolatedAsyncioTestCase):
    """Tiny integration-level checks without real HTTP calls."""

    async def test_config_flow_creates_entry_for_valid_unit_id(self) -> None:
        """The user step should create an entry for non-empty unit id."""
        flow = PukRumiaConfigFlow()
        flow.async_set_unique_id = AsyncMock()
        setattr(flow, "_abort_if_unique_id_configured", MagicMock())
        flow.async_create_entry = MagicMock(
            return_value={"type": "create_entry", "data": {CONF_UNIT_ID: "unit-1"}}
        )

        result = await flow.async_step_user({CONF_UNIT_ID: "unit-1"})

        flow.async_set_unique_id.assert_awaited_once_with("unit-1")
        flow.async_create_entry.assert_called_once()
        self.assertEqual(result["type"], "create_entry")

    def test_sensor_exposes_next_pickup_date(self) -> None:
        """Sensor native value should be a date for the bin's next pickup."""
        bin_definition = BinDefinition(
            bin_id=309,
            name="Zmieszane odpady komunalne",
            waste_type="BLACK",
            color="#2a2e34",
        )
        coordinator = MagicMock()
        coordinator.data = SimpleNamespace(
            bins={309: bin_definition},
            next_pickups={309: date(2026, 7, 21)},
        )
        coordinator.last_update_success = True
        coordinator.async_add_listener = MagicMock(return_value=lambda: None)

        entity = PukRumiaPickupSensor(coordinator, "entry-1", bin_definition)

        self.assertEqual(entity.native_value, date(2026, 7, 21))
