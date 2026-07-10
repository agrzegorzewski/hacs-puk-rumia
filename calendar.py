"""Calendar platform for PUK Rumia trash pickup integration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date, datetime
from typing import Protocol

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

try:
    from .const import DOMAIN
    from .parsing import BinDefinition
except ImportError:  # pragma: no cover - local test fallback
    from const import DOMAIN
    from parsing import BinDefinition


# Short names used only in calendar event summaries for brevity
_SHORT_BIN_NAMES: Mapping[str, str] = {
    "Zmieszane odpady komunalne": "Zmieszane",
    "Papier i tektura": "Papier",
    "Odpady biodegradowalne": "Bio",
    "Odpady segregowane": "Segregowane",
    "Tworzywa sztuczne i metale": "Plastik",
    "Szkło": "Szkło",
    "Popiół": "Popiół",
    "Odpady wielkogabarytowe": "Wielkogabarytowe",
    "Odpady zielone": "Zielone",
    "Elektroodpady": "Elektro",
}


class _CoordinatorDataLike(Protocol):
    bins: Mapping[int, BinDefinition]
    pickup_dates: Mapping[int, list[date]]


class _PickupCoordinatorLike(Protocol):
    data: _CoordinatorDataLike
    last_update_success: bool
    async_add_listener: Callable[[Callable[[], None]], CALLBACK_TYPE]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up trash pickup calendars for each waste bin."""
    coordinator: _PickupCoordinatorLike = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PukRumiaPickupCalendar(coordinator, entry.entry_id, bin_definition)
        for bin_definition in coordinator.data.bins.values()
    ]
    async_add_entities(entities)


class PukRumiaPickupCalendar(CalendarEntity):
    """Calendar entity exposing upcoming pickup dates for one waste type."""

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
        self._attr_unique_id = f"{entry_id}_{bin_definition.bin_id}_pickup_calendar"
        self._attr_name = f"{bin_definition.name} Calendar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="PUK Rumia Trash Pickup",
            manufacturer="sisms.pl",
            model="Unit timetable",
        )
        self._attr_initial_color = self._bin.color
        self._event: CalendarEvent | None = None
        self._update_attrs()

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming pickup event."""
        return self._event

    def _build_event(self, pickup_date: date) -> CalendarEvent:
        """Build a calendar event for a pickup date."""
        short_name = _SHORT_BIN_NAMES.get(self._bin.name, self._bin.name)
        return CalendarEvent(
            start=pickup_date,
            end=pickup_date,
            summary=short_name,
            description=f"Rodzaj odpadu: {self._bin.name}",
        )

    def _update_attrs(self) -> None:
        """Refresh calendar state from coordinator data."""
        self._attr_available = self.coordinator.last_update_success
        pickup_dates = self.coordinator.data.pickup_dates.get(self._bin.bin_id, [])
        self._event = self._build_event(pickup_dates[0]) if pickup_dates else None

    async def async_added_to_hass(self) -> None:
        """Register coordinator listener when entity is added."""
        self._unsub_coordinator = self.coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister coordinator listener when entity is removed."""
        await super().async_will_remove_from_hass()
        if self._unsub_coordinator is not None:
            self._unsub_coordinator()
            self._unsub_coordinator = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle fresh coordinator data."""
        self._update_attrs()
        self.async_write_ha_state()

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return pickup events within a datetime range."""
        del hass
        start = start_date.date()
        end = end_date.date()
        pickup_dates = self.coordinator.data.pickup_dates.get(self._bin.bin_id, [])
        return [
            self._build_event(pickup_date)
            for pickup_date in pickup_dates
            if start <= pickup_date < end
        ]
