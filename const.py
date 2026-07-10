"""Constants for the PUK Rumia trash pickup integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "puk_rumia"
CONF_UNIT_ID = "unit_id"
API_PARAM_UNIT_ID = "unitId"
OWNER_ID = 44

BINS_ENDPOINT = f"https://gateway.sisms.pl/akun/api/owners/{OWNER_ID}/bins/list"
TIMETABLE_ENDPOINT = (
    f"https://gateway.sisms.pl/akun/api/owners/{OWNER_ID}/timetable/get"
)

UPDATE_INTERVAL = timedelta(hours=6)
NOTIFICATION_ID_PREFIX = f"{DOMAIN}_api_error"
SOFT_WARNING_NOTIFICATION_ID_PREFIX = f"{DOMAIN}_soft_warning"

VIRTUAL_SEGREGATED_BIN_ID = -1
VIRTUAL_SEGREGATED_BIN_NAME = "Odpady segregowane"
SEGREGATED_SOURCE_BIN_NAMES = frozenset(
    {
        "Szkło",
        "Papier i tektura",
        "Tworzywa sztuczne i metale",
    }
)
