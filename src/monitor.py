"""Live terminal monitor. Run from the repository root with python -m src.monitor."""

import argparse
import math
import time
from datetime import datetime
from pathlib import Path

from .sensor_reader import DEFAULT_DEVICES_DIR, SensorReadError, read_temperature_c


def main(argv=None):
    parser = argparse.ArgumentParser(description="Monitor one DS18B20 temperature probe.")
    parser.add_argument("--threshold", type=float, default=30.0, help="warning threshold in °C (default: 30)")
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between samples (default: 2)")
    parser.add_argument("--devices-dir", type=Path, default=DEFAULT_DEVICES_DIR,
                        help="1-Wire devices directory (defaults to the Linux bus)")
    args = parser.parse_args(argv)
    if not math.isfinite(args.threshold):
        parser.error("--threshold must be finite")
    if not math.isfinite(args.interval) or args.interval <= 0:
        parser.error("--interval must be positive and finite")

    try:
        print(f"Threshold: {args.threshold:g} °C | Interval: {args.interval:g} s | Ctrl+C to stop", flush=True)
        while True:
            started = time.monotonic()
            try:
                temperature = read_temperature_c(args.devices_dir)
            except SensorReadError as exc:
                message = f"SENSOR ERROR  {exc}"
            else:
                status = "WARNING" if temperature > args.threshold else "NORMAL"
                message = f"{temperature:.3f} °C  {status}"
            print(f"{datetime.now():%H:%M:%S}  {message}", flush=True)
            time.sleep(max(0, args.interval - (time.monotonic() - started)))
    except KeyboardInterrupt:
        print("\nMonitor stopped.", flush=True)


if __name__ == "__main__":
    main()
