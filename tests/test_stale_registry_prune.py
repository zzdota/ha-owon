"""Tests for stale entity registry pruning (model re-identification cleanup)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))

from owon import sensor_321


class FakeRegistry:
    """Minimal stand-in for homeassistant entity Registry."""

    def __init__(self, entries: list[SimpleNamespace]) -> None:
        self.entries = entries
        self.removed: list[str] = []

    @staticmethod
    def async_entries_for_config_entry(registry, config_entry_id):
        return registry.entries

    def async_remove(self, entity_id: str) -> None:
        self.removed.append(entity_id)


def _entry(unique_id: str, entity_id: str) -> SimpleNamespace:
    return SimpleNamespace(unique_id=unique_id, entity_id=entity_id)


def test_prune_generic_removes_previous_scheme_entries(monkeypatch) -> None:
    """Stale entries from an old key scheme are removed; current keys kept.

    Regression for duplicated/unavailable entities such as a stale
    "总电流" left over after a PC4713 device replaced its 321-style keys.
    """
    registry = FakeRegistry(
        [
            # Old 321-style keys for the device (stale after 4713 switch)
            _entry("SN1_voltage_a", "sensor.owon_pct321_sn1_phase_a_voltage"),
            _entry("SN1_current_total", "sensor.owon_pct321_sn1_current_total"),
            # Current 4713 keys (must survive)
            _entry("SN1_4713_cur_t", "sensor.meter_sn1_total_current"),
            _entry("SN1_4713_volt_an", "sensor.meter_sn1_phase_a_voltage"),
            # Other devices must never be touched
            _entry("SN2_voltage_a", "sensor.other_sn2_phase_a_voltage"),
            # 4713 sub keys keep the scheme
            _entry("SN1_4713_freq", "sensor.meter_sn1_frequency"),
        ]
    )
    monkeypatch.setattr(sensor_321.er, "async_get", lambda hass: registry)
    monkeypatch.setattr(
        sensor_321.er,
        "async_entries_for_config_entry",
        FakeRegistry.async_entries_for_config_entry,
    )

    sensor_321._prune_stale_registry_entries(
        object(), "entry-1", "SN1", {"4713_cur_t", "4713_volt_an", "4713_freq"}
    )

    assert sorted(registry.removed) == [
        "sensor.owon_pct321_sn1_current_total",
        "sensor.owon_pct321_sn1_phase_a_voltage",
    ]


def test_prune_generic_keeps_everything_when_scheme_matches(monkeypatch) -> None:
    """A 321 device with matching keys loses nothing (no regression)."""
    keys = {f"{key}" for key in ("voltage_a", "current_total", "frequency")}
    registry = FakeRegistry(
        [
            _entry(f"SN321_{key}", f"sensor.owon_pct321_sn321_{key}")
            for key in keys
        ]
    )
    monkeypatch.setattr(sensor_321.er, "async_get", lambda hass: registry)
    monkeypatch.setattr(
        sensor_321.er,
        "async_entries_for_config_entry",
        FakeRegistry.async_entries_for_config_entry,
    )

    sensor_321._prune_stale_registry_entries(
        object(), "entry-1", "SN321", keys, key_prefix="_"
    )

    assert registry.removed == []


def test_prune_341_wrapper_narrows_to_sub_prefix(monkeypatch) -> None:
    """341 sub-circuit pruning only touches ``341_sub`` unique ids."""
    registry = FakeRegistry(
        [
            _entry("SN341_341_sub3_power", "sensor.s1"),
            _entry("SN341_341_sub3_current", "sensor.s2"),
            _entry("SN341_341_sub9_power", "sensor.stale"),
            _entry("SN341_voltage_a", "sensor.s3"),
        ]
    )
    monkeypatch.setattr(sensor_321.er, "async_get", lambda hass: registry)
    monkeypatch.setattr(
        sensor_321.er,
        "async_entries_for_config_entry",
        FakeRegistry.async_entries_for_config_entry,
    )

    sensor_321._prune_stale_341_subcircuit_registry_entries(
        object(), "entry-1", "SN341", {"341_sub3_power", "341_sub3_current"}
    )

    assert registry.removed == ["sensor.stale"]
