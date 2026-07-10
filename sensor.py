"""Sensor platform for PUK Rumia trash pickup integration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

try:
    from .const import DOMAIN
    from .parsing import BinDefinition
except ImportError:  # pragma: no cover - local test fallback
    from const import DOMAIN
    from parsing import BinDefinition


class _CoordinatorDataLike(Protocol):
    bins: Mapping[int, BinDefinition]
    next_pickups: Mapping[int, date]


class _PickupCoordinatorLike(Protocol):
    data: _CoordinatorDataLike
    last_update_success: bool
    async_add_listener: Callable[[Callable[[], None]], CALLBACK_TYPE]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up trash pickup date sensors for each waste bin."""
    coordinator: _PickupCoordinatorLike = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PukRumiaPickupSensor(coordinator, entry.entry_id, bin_definition)
        for bin_definition in coordinator.data.bins.values()
    ]
    async_add_entities(entities)


class PukRumiaPickupSensor(
    SensorEntity,
):
    """Date sensor representing the next pickup for one waste type."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:trash-can-outline"

    def __init__(
        self,
        coordinator: _PickupCoordinatorLike,
        entry_id: str,
        bin_definition: BinDefinition,
    ) -> None:
        self.coordinator = coordinator
        self._unsub_coordinator: CALLBACK_TYPE | None = None
        self._bin = bin_definition
        self._attr_available: bool = True
        self._attr_native_value: StateType | date | datetime | Decimal = None
        self._attr_extra_state_attributes: dict[str, int | str | None] = {}
        self._attr_unique_id = f"{entry_id}_{bin_definition.bin_id}_pickup_date"
        self._attr_name = f"{bin_definition.name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="PUK Rumia Trash Pickup",
            manufacturer="sisms.pl",
            model="Unit timetable",
        )
        self._update_attrs()

    def _update_attrs(self) -> None:
        """Refresh sensor state from coordinator data."""
        self._attr_available = self.coordinator.last_update_success
        self._attr_native_value = self.coordinator.data.next_pickups.get(
            self._bin.bin_id
        )
        self._attr_extra_state_attributes = {
            "bin_id": self._bin.bin_id,
            "waste_type": self._bin.waste_type,
            "color": self._bin.color,
        }

    async def async_added_to_hass(self) -> None:
        """Register coordinator listener when entity is added."""
        self._unsub_coordinator = self.coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister coordinator listener when entity is removed."""
        if self._unsub_coordinator is not None:
            self._unsub_coordinator()
            self._unsub_coordinator = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle fresh coordinator data."""
        self._update_attrs()
        self.async_write_ha_state()
