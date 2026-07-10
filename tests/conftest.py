"""Test configuration for local module imports."""

from __future__ import annotations

import sys
from types import ModuleType
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _register_homeassistant_stubs() -> None:
    """Register minimal Home Assistant stubs used by local tests."""
    if "homeassistant" in sys.modules:
        return

    homeassistant = ModuleType("homeassistant")
    components_mod = ModuleType("homeassistant.components")
    helpers_mod = ModuleType("homeassistant.helpers")

    config_entries = ModuleType("homeassistant.config_entries")

    class _Handlers:
        def register(self, _domain: str) -> Callable[[type], type]:
            def _decorator(cls: type) -> type:
                return cls

            return _decorator

    class ConfigFlow:
        async def async_set_unique_id(self, _unique_id: str) -> None:
            return None

        def _abort_if_unique_id_configured(self) -> None:
            return None

        def async_create_entry(
            self, title: str, data: dict[str, Any]
        ) -> dict[str, Any]:
            return {"type": "create_entry", "title": title, "data": data}

        def async_show_form(
            self, step_id: str, data_schema: Any, errors: dict[str, str]
        ) -> dict[str, Any]:
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors,
            }

    class ConfigEntry:
        entry_id = "entry"
        data: dict[str, Any] = {}

    setattr(config_entries, "ConfigFlow", ConfigFlow)
    setattr(config_entries, "ConfigFlowResult", dict[str, Any])
    setattr(config_entries, "ConfigEntry", ConfigEntry)
    setattr(config_entries, "HANDLERS", _Handlers())

    sensor_mod = ModuleType("homeassistant.components.sensor")
    calendar_mod = ModuleType("homeassistant.components.calendar")

    class _SensorDeviceClass:
        DATE = "date"

    class SensorEntity:
        def async_write_ha_state(self) -> None:
            return None

        @property
        def native_value(self) -> Any:
            return getattr(self, "_attr_native_value", None)

    setattr(sensor_mod, "SensorDeviceClass", _SensorDeviceClass)
    setattr(sensor_mod, "SensorEntity", SensorEntity)

    class CalendarEvent:
        def __init__(
            self,
            start: Any,
            end: Any,
            summary: str,
            description: str | None = None,
        ) -> None:
            self.start = start
            self.end = end
            self.summary = summary
            self.description = description

    class CalendarEntity:
        async def async_will_remove_from_hass(self) -> None:
            return None

        def async_write_ha_state(self) -> None:
            return None

    setattr(calendar_mod, "CalendarEntity", CalendarEntity)
    setattr(calendar_mod, "CalendarEvent", CalendarEvent)

    core_mod = ModuleType("homeassistant.core")
    const_mod = ModuleType("homeassistant.const")
    aiohttp_client_mod = ModuleType("homeassistant.helpers.aiohttp_client")

    def callback(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    class HomeAssistant:
        pass

    setattr(core_mod, "CALLBACK_TYPE", Callable[..., Any])
    setattr(core_mod, "callback", callback)
    setattr(core_mod, "HomeAssistant", HomeAssistant)

    class _Platform:
        SENSOR = "sensor"
        CALENDAR = "calendar"

    async def async_get_clientsession(_hass: Any) -> Any:
        return None

    setattr(const_mod, "Platform", _Platform)
    setattr(aiohttp_client_mod, "async_get_clientsession", async_get_clientsession)

    device_registry_mod = ModuleType("homeassistant.helpers.device_registry")
    typing_mod = ModuleType("homeassistant.helpers.typing")

    class DeviceInfo(dict):
        pass

    setattr(device_registry_mod, "DeviceInfo", DeviceInfo)

    entity_platform_mod = ModuleType("homeassistant.helpers.entity_platform")
    setattr(entity_platform_mod, "AddEntitiesCallback", Callable[..., Any])
    setattr(typing_mod, "StateType", str | int | float | bool | None)

    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.components"] = components_mod
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.const"] = const_mod
    sys.modules["homeassistant.components.sensor"] = sensor_mod
    sys.modules["homeassistant.components.calendar"] = calendar_mod
    sys.modules["homeassistant.core"] = core_mod
    sys.modules["homeassistant.helpers"] = helpers_mod
    sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client_mod
    sys.modules["homeassistant.helpers.device_registry"] = device_registry_mod
    sys.modules["homeassistant.helpers.entity_platform"] = entity_platform_mod
    sys.modules["homeassistant.helpers.typing"] = typing_mod


_register_homeassistant_stubs()
