"""Tests for PC4713 support and legacy-behaviour regression."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))

import owon
from owon.const import (
    DEVICE_MODEL_321,
    DEVICE_MODEL_341,
    DEVICE_MODEL_4713,
)
from owon.sensor_4713 import (
    ALL_4713_SENSORS,
    DIAG_4713_SENSORS,
    METER_EVENT_STATE_KEYS,
    Owon4713Sensor,
    meter_fallback_name,
    parse_meter_event,
)

TRANSLATIONS_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "owon" / "translations"
LOCALES = ("en", "zh-Hans", "de", "es", "fr", "pt")


# --------------------------------------------------------------------------- #
# Model resolution regression - legacy mappings must stay untouched
# --------------------------------------------------------------------------- #


def test_legacy_model_prefixes_unchanged() -> None:
    """PC4713 additions must not alter legacy model resolution."""
    assert owon.OwonMeterDataManager._resolve_model("PC321") == DEVICE_MODEL_321
    assert owon.OwonMeterDataManager._resolve_model("PCT321") == DEVICE_MODEL_321
    assert owon.OwonMeterDataManager._resolve_model("PC341") == DEVICE_MODEL_341
    assert owon.OwonMeterDataManager._resolve_model("PCT341") == DEVICE_MODEL_341


def test_4713_model_prefixes_resolve() -> None:
    assert owon.OwonMeterDataManager._resolve_model("PC4713") == DEVICE_MODEL_4713
    assert owon.OwonMeterDataManager._resolve_model("PC4173") == DEVICE_MODEL_4713


# --------------------------------------------------------------------------- #
# Structured payload detection
# --------------------------------------------------------------------------- #


def test_structured_payload_detection() -> None:
    assert owon._is_structured_payload(
        {"type": "device.measure.energy", "command": "update", "arguments": {}}
    )
    assert owon._is_structured_payload(
        {"type": "device.info", "command": "update", "arguments": {}}
    )


def test_legacy_payloads_are_not_structured() -> None:
    """Flat DP payloads (321/341) must never take the PC4713 path."""
    assert not owon._is_structured_payload({"101": 2210, "102": 4500})
    assert not owon._is_structured_payload({"120": "3", "129": "-48"})
    assert not owon._is_structured_payload({"device_id": "SN123"})
    assert not owon._is_structured_payload(None)
    assert not owon._is_structured_payload("payload")


# --------------------------------------------------------------------------- #
# PC4713 sensor definitions
# --------------------------------------------------------------------------- #


def test_4713_sensor_definitions_complete() -> None:
    """Every protocol data dictionary key must be covered exactly once."""
    expected_keys = {
        # currents (1mA)
        "4713_cur_total": "cur_t",
        "4713_cur_a": "cur_a",
        "4713_cur_b": "cur_b",
        "4713_cur_c": "cur_c",
        # phase voltages (0.1V)
        "4713_volt_a": "volt_an",
        "4713_volt_b": "volt_bn",
        "4713_volt_c": "volt_cn",
        # average phase voltage
        "4713_volt_ln": "volt_ln",
        # frequency (0.01Hz)
        "4713_freq": "freq",
        # powers (W/VA/var)
        "4713_pwr_total": "pwr_t",
        "4713_pwr_a": "pwr_a",
        "4713_pwr_b": "pwr_b",
        "4713_pwr_c": "pwr_c",
        "4713_sva_total": "sva_t",
        "4713_sva_a": "sva_a",
        "4713_sva_b": "sva_b",
        "4713_sva_c": "sva_c",
        "4713_var_total": "var_t",
        "4713_var_a": "var_a",
        "4713_var_b": "var_b",
        "4713_var_c": "var_c",
        # power factor (0.01)
        "4713_pf_total": "pf_t",
        "4713_pf_a": "pf_a",
        "4713_pf_b": "pf_b",
        "4713_pf_c": "pf_c",
        # energies (Wh)
        "4713_wh_imp_total": "wh_imp_t",
        "4713_wh_imp_a": "wh_imp_a",
        "4713_wh_imp_b": "wh_imp_b",
        "4713_wh_imp_c": "wh_imp_c",
        "4713_wh_exp_total": "wh_exp_t",
        "4713_wh_exp_a": "wh_exp_a",
        "4713_wh_exp_b": "wh_exp_b",
        "4713_wh_exp_c": "wh_exp_c",
        # energies (VAh)
        "4713_vah_imp_total": "vah_imp_t",
        "4713_vah_imp_a": "vah_imp_a",
        "4713_vah_imp_b": "vah_imp_b",
        "4713_vah_imp_c": "vah_imp_c",
        "4713_vah_exp_total": "vah_exp_t",
        "4713_vah_exp_a": "vah_exp_a",
        "4713_vah_exp_b": "vah_exp_b",
        "4713_vah_exp_c": "vah_exp_c",
        # reactive quadrants (varh)
        "4713_varh_q1_total": "varh_q1_t",
        "4713_varh_q1_a": "varh_q1_a",
        "4713_varh_q1_b": "varh_q1_b",
        "4713_varh_q1_c": "varh_q1_c",
        "4713_varh_q2_total": "varh_q2_t",
        "4713_varh_q2_a": "varh_q2_a",
        "4713_varh_q2_b": "varh_q2_b",
        "4713_varh_q2_c": "varh_q2_c",
        "4713_varh_q3_total": "varh_q3_t",
        "4713_varh_q3_a": "varh_q3_a",
        "4713_varh_q3_b": "varh_q3_b",
        "4713_varh_q3_c": "varh_q3_c",
        "4713_varh_q4_total": "varh_q4_t",
        "4713_varh_q4_a": "varh_q4_a",
        "4713_varh_q4_b": "varh_q4_b",
        "4713_varh_q4_c": "varh_q4_c",
        # diagnostics
        "4713_device_id": "device_id",
        "4713_device_model": "device_model",
        "4713_device_sub_model": "device_sub_model",
        "4713_firmware_version": "firmware_version",
        "4713_device_name": "device_name",
        "4713_meter_event": "evt",
    }
    actual = {desc.key: desc.data_key for desc in ALL_4713_SENSORS}
    assert actual == expected_keys
    assert len(ALL_4713_SENSORS) == 63


def test_4713_unique_ids_and_translation_keys() -> None:
    keys = [desc.key for desc in ALL_4713_SENSORS]
    assert len(keys) == len(set(keys)), "duplicate entity keys"
    tkeys = [desc.translation_key for desc in ALL_4713_SENSORS]
    assert all(tk for tk in tkeys), "every entity needs a translation_key"


def test_4713_units_and_scales() -> None:
    by_key = {desc.key: desc for desc in ALL_4713_SENSORS}

    cur_a = by_key["4713_cur_a"]
    assert cur_a.data_key == "cur_a"
    assert cur_a.scale == 0.001
    assert cur_a.device_class == "current"

    volt_a = by_key["4713_volt_a"]
    assert volt_a.data_key == "volt_an"
    assert volt_a.scale == 0.1

    freq = by_key["4713_freq"]
    assert freq.scale == 0.01

    pwr_t = by_key["4713_pwr_total"]
    assert pwr_t.scale == 0.001
    assert pwr_t.native_unit_of_measurement == "kW"

    pf_t = by_key["4713_pf_total"]
    assert pf_t.scale == 0.01
    assert pf_t.native_unit_of_measurement is None

    wh_imp = by_key["4713_wh_imp_total"]
    assert wh_imp.state_class == "total_increasing"
    assert wh_imp.native_unit_of_measurement == "kWh"

    kvarh = by_key["4713_varh_q1_total"]
    assert kvarh.native_unit_of_measurement == "kvarh"


def test_4713_energy_sensors_are_total_increasing() -> None:
    energy_keys = (
        "4713_wh_imp_total",
        "4713_wh_exp_total",
        "4713_vah_imp_total",
        "4713_vah_exp_total",
        "4713_varh_q1_total",
        "4713_varh_q4_c",
    )
    by_key = {desc.key: desc for desc in ALL_4713_SENSORS}
    for key in energy_keys:
        assert by_key[key].state_class == "total_increasing"


def test_parse_meter_event() -> None:
    assert parse_meter_event(0) == "normal"
    assert parse_meter_event(1) == "phase_a_sequence_abnormal"
    assert parse_meter_event(2) == "phase_b_sequence_abnormal"
    assert parse_meter_event(4) == "phase_c_sequence_abnormal"
    assert parse_meter_event(3) == "phase_a_b_sequence_abnormal"
    assert parse_meter_event(5) == "phase_a_c_sequence_abnormal"
    assert parse_meter_event(6) == "phase_b_c_sequence_abnormal"
    assert parse_meter_event(7) == "phase_a_b_c_sequence_abnormal"
    assert parse_meter_event(2048) == "unknown"
    assert parse_meter_event(-1) == "normal"
    assert parse_meter_event(None) == "unknown"
    assert parse_meter_event("abc") == "unknown"


# --------------------------------------------------------------------------- #
# Translations
# --------------------------------------------------------------------------- #


def test_4713_translations_cover_all_entities() -> None:
    """Every 4713 translation key must exist in every locale file."""
    translation_keys = {
        desc.translation_key
        for desc in ALL_4713_SENSORS
        if desc.translation_key is not None
    }
    for locale in LOCALES:
        payload = json.loads((TRANSLATIONS_DIR / f"{locale}.json").read_text())
        sensors = payload["entity"]["sensor"]
        missing = [key for key in translation_keys if key not in sensors]
        assert not missing, f"{locale} missing: {missing}"


def test_4713_translation_spot_checks() -> None:
    expected = {
        "en": {
            "voltage_avg": "Average phase voltage",
            "meter_device_sub_model": "3 Device sub model",
            "phase_sequence_status": "6 Phase sequence status",
            "device_name": "5 Device name",
        },
        "zh-Hans": {
            "voltage_avg": "相电压平均值",
            "meter_device_sub_model": "3 设备子类型",
            "phase_sequence_status": "6 相序状态",
            "device_name": "5 设备名称",
        },
    }
    for locale, names in expected.items():
        payload = json.loads((TRANSLATIONS_DIR / f"{locale}.json").read_text())
        for key, name in names.items():
            assert payload["entity"]["sensor"][key]["name"] == name


def test_legacy_translations_unchanged() -> None:
    """Existing 321/341 translations must keep their original values."""
    expected_names = {
        "en": {
            "energy_consumed_a": "Phase A forward energy",
            "reverse_energy_a": "Phase A reverse energy",
            "energy_consumed_total": "Total forward energy",
            "reverse_energy_total": "Total reverse energy",
            "voltage_a": "Phase A voltage",
            "current_total": "Total current",
        },
        "zh-Hans": {
            "energy_consumed_a": "A相正向累计电量",
            "reverse_energy_a": "A相反向累计电量",
            "energy_consumed_total": "总累计电量",
            "reverse_energy_total": "总反向累计电量",
            "voltage_a": "A相电压",
            "current_total": "总电流",
        },
    }
    for locale, names in expected_names.items():
        payload = json.loads((TRANSLATIONS_DIR / f"{locale}.json").read_text())
        for key, name in names.items():
            assert payload["entity"]["sensor"][key]["name"] == name


# --------------------------------------------------------------------------- #
# device_info merge & fallback name
# --------------------------------------------------------------------------- #


def test_merge_4713_device_info_structured_after_discovery() -> None:
    """Structured device.info arriving after discovery must keep subModel."""
    current = {
        "class": "Meter",
        "model": "PC4713",
        "subModel": "-w-485",
        "manufacturer": "OWON",
        "fw_version": "V0.0.3",
        "protocol_version": 1,
    }
    owon.merge_4713_device_info(
        current,
        {
            "sn": "SN123",
            "model": "PC4713",
            "version": "V0.0.3",
            "options": "WiFi,485",
            "name": "MY_METER",
        },
        "SN123",
    )
    assert current["subModel"] == "-w-485"
    assert current["name"] == "MY_METER"
    assert current["fw_version"] == "V0.0.3"
    assert current["options"] == "WiFi,485"
    assert current["device_id"] == "SN123"


def test_merge_4713_device_info_discovery_after_structured() -> None:
    """Discovery payload arriving after structured info must keep name."""
    current = {
        "sn": "SN123",
        "model": "PC4713",
        "version": "V1.0.3",
        "options": "WiFi,485",
        "name": "REAL_NAME",
    }
    owon.merge_4713_device_info(
        current,
        {
            "class": "Meter",
            "model": "PC4713",
            "subModel": "-w-485",
            "manufacturer": "OWON",
            "fw_version": "V1.0.3",
            "protocol_version": 1,
        },
        "SN123",
    )
    assert current["name"] == "REAL_NAME"
    assert current["subModel"] == "-w-485"
    assert current["fw_version"] == "V1.0.3"
    assert current["device_id"] == "SN123"


def test_meter_fallback_name() -> None:
    assert meter_fallback_name("123456789033333") == "METER_033333"
    assert meter_fallback_name("SN12") == "METER_SN12"
    assert meter_fallback_name("123456") == "METER_123456"


def test_4713_card_name_is_full_sn() -> None:
    """The device card name is always METER_{full SN}, never device-reported."""
    desc = next(d for d in DIAG_4713_SENSORS if d.key == "4713_device_id")
    manager = SimpleNamespace(device_info={"SN123": {"name": "METER_456789"}})
    sensor = Owon4713Sensor("SN123", desc, manager)
    assert sensor.device_info["name"] == "METER_SN123"
    assert sensor.device_info["identifiers"] == {("owon", "SN123")}


def test_4713_phase_sequence_status_translations() -> None:
    """Every evt state key must be translated in every locale."""
    for locale in LOCALES:
        payload = json.loads((TRANSLATIONS_DIR / f"{locale}.json").read_text())
        states = payload["entity"]["sensor"]["phase_sequence_status"]["state"]
        missing = METER_EVENT_STATE_KEYS - set(states)
        assert not missing, f"{locale} missing states: {sorted(missing)}"
