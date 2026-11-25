import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from src.monitor import main
from src.sensor_reader import SensorReadError


class MonitorTests(unittest.TestCase):
    def run_readings(self, readings, args=()):
        output = io.StringIO()
        with patch("src.monitor.read_temperature_c", side_effect=[*readings, KeyboardInterrupt()]), \
             patch("src.monitor.time.sleep"), redirect_stdout(output):
            main(args)
        lines = output.getvalue().splitlines()
        self.assertEqual(lines[-1], "Monitor stopped.")
        return lines

    def test_boundary_warning_and_cooling(self):
        lines = self.run_readings([29.0, 30.0, 30.001, 29.0])
        self.assertIn("Threshold: 30 °C | Interval: 2 s", lines[0])
        self.assertEqual([line.split()[-1] for line in lines[1:5]],
                         ["NORMAL", "NORMAL", "WARNING", "NORMAL"])
        self.assertRegex(lines[3], r"^\d{2}:\d{2}:\d{2}  30\.001 °C  WARNING$")

    def test_error_then_recovery_with_custom_settings(self):
        lines = self.run_readings([25, SensorReadError("missing file"), 23],
                                  ["--threshold", "24", "--interval", "0.1"])
        self.assertIn("Threshold: 24 °C | Interval: 0.1 s", lines[0])
        self.assertTrue(lines[1].endswith("25.000 °C  WARNING"))
        self.assertTrue(lines[2].endswith("SENSOR ERROR  missing file"))
        self.assertNotIn("25.000", lines[2])
        self.assertTrue(lines[3].endswith("23.000 °C  NORMAL"))

    def test_invalid_settings(self):
        for flag, value in [("--interval", "0"), ("--interval", "-1"),
                            ("--interval", "inf"), ("--threshold", "nan")]:
            with self.subTest(flag=flag, value=value), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main([flag, value])
                self.assertEqual(error.exception.code, 2)
