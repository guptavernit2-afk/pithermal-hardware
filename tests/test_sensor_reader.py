import tempfile
import unittest
from pathlib import Path

from src.sensor_reader import SensorReadError, read_temperature_c


class SensorReaderTests(unittest.TestCase):
    def setUp(self):
        temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_dir.cleanup)
        self.devices = Path(temporary_dir.name)
        self.probe = self.devices / "28-0123456789ab"
        self.probe.mkdir()
        self.attribute = self.probe / "temperature"

    def test_discovers_probe_and_converts_each_new_reading(self):
        (self.devices / "w1_bus_master1").mkdir()
        (self.devices / "10-0123456789ab").mkdir()
        for raw, expected in [(26500, 26.5), (0, 0.0), (-5500, -5.5),
                              (-55000, -55.0), (125000, 125.0), (62, 0.062)]:
            with self.subTest(raw=raw):
                self.attribute.write_bytes(f"{raw}\n".encode("ascii"))
                self.assertEqual(read_temperature_c(self.devices), expected)

    def test_missing_bus_directory(self):
        with self.assertRaisesRegex(SensorReadError, "Cannot access"):
            read_temperature_c(self.devices / "missing")

    def test_missing_probe_ignores_unrelated_entries(self):
        self.probe.rmdir()
        self.probe.touch()
        (self.devices / "w1_bus_master1").mkdir()
        (self.devices / "28-invalid").mkdir()
        with self.assertRaisesRegex(SensorReadError, "No DS18B20"):
            read_temperature_c(self.devices)

    def test_multiple_probes_report_ambiguity(self):
        (self.devices / "28-fedcba987654").mkdir()
        with self.assertRaisesRegex(SensorReadError, "found 2"):
            read_temperature_c(self.devices)

    def test_missing_temperature_file(self):
        with self.assertRaisesRegex(SensorReadError, "Cannot read"):
            read_temperature_c(self.devices)

    def test_invalid_contents(self):
        for raw in (b"", b"\n", b"26.5", b"26_500", b"not available", b"\xff"):
            with self.subTest(raw=raw):
                self.attribute.write_bytes(raw)
                with self.assertRaisesRegex(SensorReadError, "Invalid millidegree"):
                    read_temperature_c(self.devices)

    def test_out_of_range_readings(self):
        for raw in (b"-55001", b"125001"):
            with self.subTest(raw=raw):
                self.attribute.write_bytes(raw)
                with self.assertRaisesRegex(SensorReadError, "outside its temperature range"):
                    read_temperature_c(self.devices)

    def test_failure_after_success_and_recovery(self):
        self.attribute.write_bytes(b"19000")
        self.assertEqual(read_temperature_c(self.devices), 19.0)
        self.attribute.unlink()
        with self.assertRaises(SensorReadError):
            read_temperature_c(self.devices)
        self.attribute.write_bytes(b"21000")
        self.assertEqual(read_temperature_c(self.devices), 21.0)
