"""Data update coordinator for PUK Rumia pickup data."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date
import logging
from typing import Any, cast

from aiohttp import ClientError, ClientSession, ClientTimeout

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

try:
    from .const import (
        API_PARAM_UNIT_ID,
        BINS_ENDPOINT,
        DOMAIN,
        NOTIFICATION_ID_PREFIX,
        SEGREGATED_SOURCE_BIN_NAMES,
        SOFT_WARNING_NOTIFICATION_ID_PREFIX,
        TIMETABLE_ENDPOINT,
        UPDATE_INTERVAL,
        VIRTUAL_SEGREGATED_BIN_ID,
        VIRTUAL_SEGREGATED_BIN_NAME,
    )
    from .parsing import (
        BinDefinition,
        add_virtual_bin_from_names,
        extract_bins,
        extract_pickup_dates,
    )
except ImportError:  # pragma: no cover - local test fallback
    from const import (
        API_PARAM_UNIT_ID,
        BINS_ENDPOINT,
        DOMAIN,
        NOTIFICATION_ID_PREFIX,
        SEGREGATED_SOURCE_BIN_NAMES,
        SOFT_WARNING_NOTIFICATION_ID_PREFIX,
        TIMETABLE_ENDPOINT,
        UPDATE_INTERVAL,
        VIRTUAL_SEGREGATED_BIN_ID,
        VIRTUAL_SEGREGATED_BIN_NAME,
    )
    from parsing import (
        BinDefinition,
        add_virtual_bin_from_names,
        extract_bins,
        extract_pickup_dates,
    )

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CoordinatorData:
    """Combined data needed by sensor entities."""

    bins: dict[int, BinDefinition]
    next_pickups: dict[int, date]
    pickup_dates: dict[int, list[date]]


class PukRumiaDataUpdateCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Coordinate API polling and payload parsing."""

    def __init__(
        self,
        hass: HomeAssistant,
        unit_id: str,
        session: ClientSession,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{unit_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.unit_id = unit_id
        self._session = session

    @property
    def notification_id(self) -> str:
        """Return the persistent notification id for this config entry."""
        return f"{NOTIFICATION_ID_PREFIX}_{self.unit_id}"

    @property
    def soft_warning_notification_id(self) -> str:
        """Return the persistent soft-warning notification id for this config entry."""
        return f"{SOFT_WARNING_NOTIFICATION_ID_PREFIX}_{self.unit_id}"

    async def _async_fetch_json(self, endpoint: str) -> dict[str, Any]:
        """Fetch JSON payload from SISMS API endpoint."""
        async with self._session.get(
            endpoint,
            params={API_PARAM_UNIT_ID: self.unit_id},
            timeout=ClientTimeout(total=20),
        ) as response:
            response.raise_for_status()
            payload = await response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response is not a JSON object")
            return cast(dict[str, Any], payload)

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch, validate and combine bins and timetable data."""
        try:
            bins_payload, timetable_payload = await asyncio.gather(
                self._async_fetch_json(BINS_ENDPOINT),
                self._async_fetch_json(TIMETABLE_ENDPOINT),
            )
            bins = extract_bins(bins_payload)
            if not bins:
                raise ValueError("Bins endpoint returned no valid bins")

            pickup_dates = extract_pickup_dates(timetable_payload)
            next_pickups = {
                bin_id: dates[0] for bin_id, dates in pickup_dates.items() if dates
            }
            bins, next_pickups, mismatch_details = add_virtual_bin_from_names(
                bins,
                next_pickups,
                source_bin_names=SEGREGATED_SOURCE_BIN_NAMES,
                virtual_bin_id=VIRTUAL_SEGREGATED_BIN_ID,
                virtual_bin_name=VIRTUAL_SEGREGATED_BIN_NAME,
                virtual_waste_type="SEGREGATED",
            )
            if (virtual_next_pickup := next_pickups.get(VIRTUAL_SEGREGATED_BIN_ID)) is not None:
                pickup_dates[VIRTUAL_SEGREGATED_BIN_ID] = [virtual_next_pickup]
            data = CoordinatorData(
                bins=bins,
                next_pickups=next_pickups,
                pickup_dates=pickup_dates,
            )

            persistent_notification.async_dismiss(self.hass, self.notification_id)
            if mismatch_details is None:
                persistent_notification.async_dismiss(
                    self.hass, self.soft_warning_notification_id
                )
            else:
                warning_message = (
                    "Detected mismatch in segregated waste pickup dates for "
                    f"unitId={self.unit_id}: {mismatch_details}. "
                    "Virtual bin 'Odpady segregowane' uses the earliest available date."
                )
                _LOGGER.warning(warning_message)
                persistent_notification.async_create(
                    self.hass,
                    warning_message,
                    title="PUK Rumia integration warning",
                    notification_id=self.soft_warning_notification_id,
                )
            return data
        except (ClientError, asyncio.TimeoutError, ValueError) as err:
            message = (
                "Unable to refresh PUK Rumia trash pickup data for "
                f"unitId={self.unit_id}. Error: {err}"
            )
            persistent_notification.async_create(
                self.hass,
                message,
                title="PUK Rumia integration update failed",
                notification_id=self.notification_id,
            )
            raise UpdateFailed(message) from err
