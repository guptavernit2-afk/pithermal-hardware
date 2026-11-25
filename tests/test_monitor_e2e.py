"""Launch the real monitor with a temporary sensor. Run this file to see the demo."""

import asyncio
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMAND = (sys.executable, "-B", "-X", "utf8", "-m", "src.monitor")


class LiveMonitorTests(unittest.IsolatedAsyncioTestCase):
    async def test_live_sensor_sequence(self):
        with tempfile.TemporaryDirectory() as directory:
            probe = Path(directory) / "28-0123456789ab"
            probe.mkdir()
            reading = probe / "temperature"
            reading.write_text("27000", encoding="ascii")

            monitor = await asyncio.create_subprocess_exec(
                *COMMAND, "--devices-dir", directory, "--threshold", "28", "--interval", "0.2",
                cwd=ROOT, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
            )
            try:
                async def next_line():
                    raw = await monitor.stdout.readline()
                    self.assertTrue(raw, "Monitor exited before the demo finished")
                    line = raw.decode("utf-8").rstrip()
                    if __name__ == "__main__":
                        print(line, flush=True)
                    return line

                header = await asyncio.wait_for(next_line(), timeout=10)
                self.assertIn("Threshold: 28 °C | Interval: 0.2 s", header)
                previous = None
                for raw, expected in [
                    (27000, "27.000 °C  NORMAL"),
                    (28000, "28.000 °C  NORMAL"),
                    (28001, "28.001 °C  WARNING"),
                    (27500, "27.500 °C  NORMAL"),
                    (None, "SENSOR ERROR"),
                    (26500, "26.500 °C  NORMAL"),
                ]:
                    if raw is None:
                        reading.unlink()
                    elif previous is not None:
                        pending = probe / "next-reading"
                        pending.write_text(str(raw), encoding="ascii")
                        pending.replace(reading)

                    # A sample from just before the change may already be in the pipe.
                    async def observe_change():
                        while True:
                            line = await next_line()
                            self.assertRegex(line, r"^\d{2}:\d{2}:\d{2}  ")
                            message = line[10:]
                            if previous is not None and message == previous:
                                continue
                            if raw is None:
                                self.assertTrue(message.startswith("SENSOR ERROR  "), message)
                            else:
                                self.assertEqual(message, expected)
                            return message

                    previous = await asyncio.wait_for(observe_change(), timeout=5)
            finally:
                if monitor.returncode is None:
                    monitor.kill()
                await monitor.communicate()

    async def test_invalid_interval_exits_with_usage_error(self):
        monitor = await asyncio.create_subprocess_exec(
            *COMMAND, "--interval", "0", cwd=ROOT,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(monitor.communicate(), timeout=10)
        finally:
            if monitor.returncode is None:
                monitor.kill()
                await monitor.communicate()
        self.assertEqual(monitor.returncode, 2)
        self.assertEqual(stdout, b"")
        self.assertIn(b"--interval must be positive and finite", stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
