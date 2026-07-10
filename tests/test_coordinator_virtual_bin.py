"""Coordinator tests for virtual segregated waste bin behavior."""

from __future__ import annotations

from datetime import date
import unittest

from const import (
    SEGREGATED_SOURCE_BIN_NAMES,
    VIRTUAL_SEGREGATED_BIN_ID,
    VIRTUAL_SEGREGATED_BIN_NAME,
)
from parsing import BinDefinition
from parsing import add_virtual_bin_from_names


class TestCoordinatorVirtualBin(unittest.TestCase):
    """Validate virtual bin creation and mismatch warnings."""

    def test_adds_virtual_bin_when_source_bins_exist(self) -> None:
        bins = {
            1: BinDefinition(1, "Szkło", "GLASS", "#123456"),
            2: BinDefinition(2, "Papier i tektura", "PAPER", "#111111"),
            3: BinDefinition(3, "Tworzywa sztuczne i metale", "PLASTIC", "#222222"),
        }
        next_pickups = {
            1: date(2026, 7, 20),
            2: date(2026, 7, 20),
            3: date(2026, 7, 20),
        }

        bins_out, next_pickups_out, mismatch = add_virtual_bin_from_names(
            bins,
            next_pickups,
            source_bin_names=SEGREGATED_SOURCE_BIN_NAMES,
            virtual_bin_id=VIRTUAL_SEGREGATED_BIN_ID,
            virtual_bin_name=VIRTUAL_SEGREGATED_BIN_NAME,
            virtual_waste_type="SEGREGATED",
        )

        self.assertIn(VIRTUAL_SEGREGATED_BIN_ID, bins_out)
        self.assertEqual(
            bins_out[VIRTUAL_SEGREGATED_BIN_ID].name, VIRTUAL_SEGREGATED_BIN_NAME
        )
        self.assertEqual(next_pickups_out[VIRTUAL_SEGREGATED_BIN_ID], date(2026, 7, 20))
        self.assertIsNone(mismatch)

    def test_warns_when_source_values_differ(self) -> None:
        bins = {
            1: BinDefinition(1, "Szkło", "GLASS", "#123456"),
            2: BinDefinition(2, "Papier i tektura", "PAPER", "#111111"),
            3: BinDefinition(3, "Tworzywa sztuczne i metale", "PLASTIC", "#222222"),
        }
        next_pickups = {
            1: date(2026, 7, 20),
            2: date(2026, 7, 19),
            3: date(2026, 7, 20),
        }

        _, next_pickups_out, mismatch = add_virtual_bin_from_names(
            bins,
            next_pickups,
            source_bin_names=SEGREGATED_SOURCE_BIN_NAMES,
            virtual_bin_id=VIRTUAL_SEGREGATED_BIN_ID,
            virtual_bin_name=VIRTUAL_SEGREGATED_BIN_NAME,
            virtual_waste_type="SEGREGATED",
        )

        self.assertEqual(next_pickups_out[VIRTUAL_SEGREGATED_BIN_ID], date(2026, 7, 19))
        self.assertIsNotNone(mismatch)
