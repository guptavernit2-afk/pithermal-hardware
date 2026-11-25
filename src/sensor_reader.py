"""Read a single DS18B20 through the Linux 1-Wire temperature attribute."""

import re
from pathlib import Path


DEFAULT_DEVICES_DIR = Path("/sys/bus/w1/devices")


class SensorReadError(Exception):
    """The probe could not be identified or did not supply a valid reading."""


def read_temperature_c(devices_dir: Path = DEFAULT_DEVICES_DIR) -> float:
    """Discover one DS18B20 and return its current temperature in degrees Celsius."""
    try:
        probes = [
            entry for entry in devices_dir.iterdir()
            if re.fullmatch(r"28-[0-9a-fA-F]{12}", entry.name) and entry.is_dir()
        ]
    except OSError as exc:
        raise SensorReadError(f"Cannot access 1-Wire devices in {devices_dir}: {exc}") from exc

    if not probes:
        raise SensorReadError(f"No DS18B20 found in {devices_dir}")
    if len(probes) > 1:
        raise SensorReadError(f"Expected one DS18B20 in {devices_dir}, found {len(probes)}")

    attribute = probes[0] / "temperature"
    try:
        raw = attribute.read_bytes().strip()
    except OSError as exc:
        raise SensorReadError(f"Cannot read {attribute}: {exc}") from exc

    # The driver reports whole millidegrees; the DS18B20 spans -55 to +125 °C.
    if not re.fullmatch(rb"-?[0-9]{1,6}", raw):
        raise SensorReadError(f"Invalid millidegree reading in {attribute}")
    millidegrees = int(raw)
    if not -55_000 <= millidegrees <= 125_000:
        raise SensorReadError(f"DS18B20 reading outside its temperature range: {millidegrees} m°C")
    return millidegrees / 1000
