"""Minimal parsing tests for PUK Rumia payload helpers."""

from __future__ import annotations

from datetime import date
import unittest

from parsing import extract_bins, extract_next_pickups, parse_iso8601_date


class TestParsing(unittest.TestCase):
    """Parser behavior should stay predictable for date payloads."""

    def test_parse_iso8601_date_accepts_date_and_datetime(self) -> None:
        """ISO date and datetime values should both produce date objects."""
        self.assertEqual(parse_iso8601_date("2026-07-09"), date(2026, 7, 9))
        self.assertEqual(
            parse_iso8601_date("2026-07-09T14:20:00+02:00"),
            date(2026, 7, 9),
        )
        self.assertEqual(
            parse_iso8601_date("2026-07-09T00:00:00Z"),
            date(2026, 7, 9),
        )

    def test_parse_iso8601_date_rejects_invalid_values(self) -> None:
        """Bad strings should raise a clear parser error."""
        with self.assertRaises(ValueError):
            parse_iso8601_date("not-a-date")

    def test_extract_bins_and_next_pickups(self) -> None:
        """Helpers should map bins and compute nearest upcoming pickup per bin."""
        bins_payload = {
            "data": [
                {"id": 309, "name": "Zmieszane", "type": "BLACK", "color": "#2a2e34"},
                {"id": 310, "name": "Papier", "type": "BLUE", "color": "#2a6fc9"},
            ]
        }
        timetable_payload = {
            "data": [
                {
                    "month": "2026-07",
                    "receptions": [
                        {"id": 1, "binId": 309, "date": "2026-07-07"},
                        {"id": 2, "binId": 309, "date": "2026-07-21"},
                        {"id": 3, "binId": 310, "date": "2026-07-08"},
                        {"id": 4, "binId": 310, "date": "2026-07-22"},
                    ],
                }
            ]
        }

        bins = extract_bins(bins_payload)
        next_pickups = extract_next_pickups(timetable_payload, today=date(2026, 7, 9))

        self.assertEqual(bins[309].name, "Zmieszane")
        self.assertEqual(bins[310].waste_type, "BLUE")
        self.assertEqual(next_pickups[309], date(2026, 7, 21))
        self.assertEqual(next_pickups[310], date(2026, 7, 22))
