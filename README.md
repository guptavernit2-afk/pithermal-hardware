# PiThermal | Raspberry Pi Temperature Monitor

**Operating Systems (1BCS304) · CCA project 13 · Hardware prototype**

PiThermal will turn a Raspberry Pi and a DS18B20 digital thermometer into a live temperature monitor. During the demo, someone can warm the probe and watch its reading rise in the terminal. When the reading crosses the chosen limit, the monitor will display a warning. The team will use this to explain how a Linux application gets information from a physical device.

**Current stage — Phase 3 laptop demo ready for review.** You can run the real terminal monitor with controlled sensor readings on a laptop. Physical wiring and readings are pending lab access. The companion circuit simulation is planned for a separate repository, `pithermal-sim`.

[Lab checklist](#lab-checklist) · [How Linux reads the sensor](#how-linux-reads-the-sensor) · [Demo and tests](#demo-and-tests) · [Team milestones](#team-milestones)

## What we plan to build

The assignment asks for regular temperature readings from a suitable sensor, a display of those readings, and an alert when the temperature exceeds a predefined threshold. Our proposed design uses one external sensor, a Python 3 program and a terminal display. The sensor measures the temperature at the probe.

| Decision | Proposed behavior |
| --- | --- |
| Sampling | Take a reading about every two seconds. Display the time, temperature in °C and status on each update. |
| Warning | Start with a configurable 30°C demo threshold. Compare the measured value before rounding it for display. Exactly 30°C is normal. |
| Recovery | Clear the warning on the first valid reading at or below the threshold. |
| Sensor error | Display `SENSOR ERROR` when a reading is missing or invalid. Retry on the next interval. Only display a temperature from a successful read. |
| Operation | Show the active threshold and interval at startup. Keep monitoring until the operator presses Ctrl+C. |

Example terminal display with a 30°C threshold:

```text
10:15:00  27.500 °C  NORMAL
10:15:02  30.000 °C  NORMAL
10:15:04  31.250 °C  WARNING
10:15:06  29.750 °C  NORMAL
```

## Lab checklist

Take this table to the lab. After speaking with the professor, record the exact board model and sensor variant here so the wiring guide matches the parts the team receives.

| Ask for | Qty | Purpose | Availability |
| --- | ---: | --- | --- |
| Raspberry Pi capable of running Raspberry Pi OS (e.g. Pi 3 or Pi 4) | 1 | Runs Linux and Python and provides the GPIO header. | Pending |
| Power supply suited to the board | 1 | Powers the Pi throughout the demo. | Pending |
| Bootable microSD card with Raspberry Pi OS, or a configured lab Pi | 1 | Provides the OS and storage for the monitor. | Pending |
| DS18B20 digital temperature sensor | 1 | Measures temperature. Record whether it is a bare part, waterproof probe or breakout module. | Pending |
| Breadboard and jumper wires suited to the connectors | 1 set | Connects sensor power, ground and data to the Pi. | Pending |
| 4.7 kΩ resistor | 1 if needed | Pulls the data line up to 3.3 V. Check whether the module already includes the pull-up. | Pending |
| Monitor and keyboard, or SSH access from a laptop | 1 access method | Lets the team configure the Pi and display live readings. | Pending |

**Questions for the professor**

- Which Pi and sensor can we borrow, and when is bench time available?
- Does the lab image have Python 3, and may we enable 1-Wire and reboot the Pi?
- Does a visible terminal warning satisfy the alert requirement? If a physical indicator is expected, which indicator can the lab provide?

## How Linux reads the sensor

```text
DS18B20 → GPIO data pin → Linux 1-Wire drivers → sensor file → Python monitor → terminal
```

The DS18B20 sends digital readings over its 1-Wire data connection. The Linux kernel manages that connection and its thermometer driver makes the measurement readable through **sysfs**, a filesystem that exposes device information to programs. Our Python program can open the sensor file in user space, read the value, convert it to °C and decide which status to display.

For example, the driver's `temperature` file represents 26.5°C as `26500` millidegrees. Each sensor has its own identifier. The reader discovers the device under `/sys/bus/w1/devices/` each time it reads.

References: [Linux thermometer driver](https://docs.kernel.org/w1/slaves/w1_therm.html) · [Raspberry Pi configuration guide](https://www.raspberrypi.com/documentation/computers/configuration.html#enable-or-disable-the-one-wire-interface)

## Planned setup and first run

1. Identify the board and sensor variant. Verify the sensor pinout against its part or module documentation before applying power. Probe wire colours can vary.
2. With the Pi powered down, connect sensor power to 3.3 V, ground to ground, and data to the selected 1-Wire pin (proposed BCM GPIO4). Include the pull-up from data to 3.3 V if needed. Record the final pin mapping and a wiring photo in `docs/`.
3. Boot Raspberry Pi OS, enable 1-Wire in `raspi-config` and reboot. Run `ls /sys/bus/w1/devices/` and look for the DS18B20 entry beginning with `28-`.
4. With one probe connected, try `cat /sys/bus/w1/devices/28-*/temperature` to check one reading independently of our program. If the device is missing, check interface configuration and wiring. If the directory exists but that attribute is unavailable, inspect the driver's `w1_slave` output and record what the lab image provides.
5. From the repository root on the Pi, run `python3 -m src.monitor`. The defaults are a 30°C threshold and a two-second interval. Override them with, for example, `python3 -m src.monitor --threshold 28 --interval 1`. Press Ctrl+C to stop.

## Demo and tests

### Run the laptop demo from a fresh checkout

Use Git and Python 3.8 or later. Run these commands from the parent folder where you want the checkout. If your system names Python 3 `python3`, use that command in place of `python`.

```sh
git clone https://github.com/guptavernit2-afk/pithermal-hardware.git
cd pithermal-hardware
python -B -m unittest discover -s tests -v
python -B -X utf8 tests/test_monitor_e2e.py
```

The first Python command runs the full suite. The second runs the end-to-end checks again and prints the monitor's live output. It starts `python -m src.monitor` with a temporary device directory, a **28°C threshold**, and a **0.2-second interval**. The test changes the input files automatically, checks the output and stops the process. There are no packages to install or readings to type.

| Input in the demo | What you should see |
| --- | --- |
| 27°C, then exactly 28°C | Both timestamped readings show `NORMAL`. |
| 28.001°C, then 27.5°C | First `WARNING`, then `NORMAL`. |
| Temperature file removed | `SENSOR ERROR` with the missing file's path. |
| File restored with 26.5°C | A fresh `26.500 °C  NORMAL` line in the same process. |

Expect **13 passing tests** in the full suite and **2 passing checks** in the demo. The second check verifies that an interval of zero exits with a usage error. If Python reports it cannot find `src.monitor`, run the command from the folder containing this README. If a manual run on your laptop reports a missing 1-Wire directory, use the demo command above. The plain monitor command defaults to the Pi's device directory.

### Phase 1 laptop verification

From the repository root, run the following with Python 3. The tests create and clean up their own temporary device directories. They require only the Python standard library.

```sh
python -B -m unittest discover -s tests -v
```

**Observed on Windows with Python 3.13.6:** all eight tests passed. Controlled inputs covered positive, zero and negative readings, the sensor's range limits, discovery among unrelated devices, multiple probes, missing files, invalid data and a fresh read after recovery from an error.

The [sensor reader](src/sensor_reader.py) exposes `read_temperature_c()`. With one connected probe it returns a temperature in °C. If the reading is unavailable, invalid or ambiguous, it raises `SensorReadError`. Production calls use Linux's device directory by default. The [tests](tests/test_sensor_reader.py) pass a temporary directory as the `devices_dir` argument.

### Monitor and bench test plan

**Phase 2 laptop results.** All 11 reader and monitor tests passed. A separate Windows run launched the monitor with `--devices-dir` pointing to a temporary 1-Wire directory and `--interval 0.25`. At a 30°C threshold, the sequence 29 → 30 → 31 → 29°C printed NORMAL → NORMAL → WARNING → NORMAL. Removing the temperature file produced SENSOR ERROR. Restoring it with 27500 millidegrees produced 27.500°C and NORMAL on the next sample in the same process.

| Check | How we will test | Expected result |
| --- | --- | --- |
| Conversion | Give the reader a test value of 26500 millidegrees. | 26.5°C. |
| Threshold boundary | Use repeatable software inputs below, exactly at and above 30°C. | Normal, normal, warning. |
| Recovery | Follow an above-limit input with a value below the limit. | Warning clears at the next reading. |
| Missing or invalid input | Supply a missing file or unreadable value, then a valid reading. | Sensor error, followed by a fresh reading. |
| Physical sensor detection | Boot the wired Pi and inspect its sensor directory. | The probe appears and produces a plausible room-temperature reading. |
| Live demonstration | Choose a threshold just above the room reading. Gently warm the probe, then allow it to cool. | Timestamped readings rise, the warning appears above the limit, then clears as the probe cools. |
| Physical sensor absent | Power down, disconnect the probe, then boot and start the monitor. | The terminal reports a sensor error. |

For each test, record the input or bench setup, expected result, observed result and pass/fail. Identify which tests used software inputs and which ran on the physical Pi. Save a wiring photo and terminal capture from the bench session for the report.

## Repository structure

```text
README.md   Project brief, equipment checklist, setup, team plan and test criteria
src/        Python sensor reader, monitoring loop and terminal output
tests/      Repeatable software tests using controlled sensor inputs
docs/       Confirmed wiring, bench evidence and final report
```

The Phase 1 reader lives in `src/`, and its laptop tests live in `tests/`. Keep setup and operating instructions in this README so teammates have one starting point.

## Team milestones

| Stage | Work and handoff | Status |
| --- | --- | --- |
| 1. Read one temperature | Discover one DS18B20, read its temperature and verify conversion and error handling. | Reviewed |
| 2. Build live monitor | Run the sampling loop, warning logic and terminal output. | Reviewed |
| 3. Test on laptop | Run the documented demo from a fresh checkout and verify warning, cooling and recovery through the real terminal command. | Ready for review |
| 4. Integrate on Pi | Hardware lead confirms pinout, enables 1-Wire, verifies a raw reading and runs the same application. Team records and fixes any integration issues. | Awaiting hardware |
| 5. Demonstrate and report | Team rehearses the live demo, collects evidence and completes the report. | Planned |

Assign a teammate to each milestone once roles are agreed. Use a GitHub issue for each task with an owner and an expected result. Link the change or test evidence when closing the issue. Everyone should be able to explain one reading from the probe to the terminal.

## CCA marks and report plan

| Criterion | Marks | Evidence to prepare |
| --- | ---: | --- |
| Fundamental knowledge | 5 | Explain GPIO, 1-Wire, the kernel driver, sysfs and the user-space program using our actual setup. |
| Implementation | 5 | Working physical demo, repeatable test cases, observed results and recovery behavior. |
| Teamwork | 5 | Contributions, reviews, joint integration and rehearsal. |
| Report | 5 | Clear objective, hardware list, wiring diagram, software design, test results, limitations, contributions and conclusion. |

**Total: 20 marks.** Record observations as work happens. Use the final report to explain what the team built, how it behaved on the bench and which design decisions changed during integration.
