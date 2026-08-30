# Hardware bring-up guide

Build and commission the Raspberry Pi edge unit. Follow the steps in order — each
one is only meaningful if the previous one passed.

> **Safety.** Stages 1 and 2 use LEDs in place of the fan and heat lamp. Do not
> connect a mains load until step 7 passes. Mains wiring is confined to the relay
> output side, behind a fuse and a breaker, inside the enclosure.

---

## What you have, and what is missing

Checked against the bill of materials in Section 3.5.1 of the dissertation.

| Component | Status | Note |
|---|---|---|
| Raspberry Pi + case | have | confirm the model with step 0 |
| 5 V power supply | have | **verify the label reads 5 V** before plugging in |
| Breadboard | have | |
| Jumper wires | have | |
| DHT22 | have | 3-pin breakout, pull-up already fitted |
| MQ135 gas sensor | have | analogue + digital outputs |
| Relay module | have | check whether it is 1- or 2-channel |
| LEDs + resistors | have | stand-ins for the actuators in stages 1–2 |
| **ADC (ADS1115 / MCP3008)** | **missing** | blocks quantitative gas readings — see below |
| **Camera** | **missing** | blocks the whole vision subsystem |
| **2nd relay channel** | **check** | you need two: fan and heater |
| Fan, heat lamp, enclosure, fuse | later | stage 3 only |

### The ADC gap

The Pi has no analogue input, so the MQ135's analogue output cannot be read
without an external converter. Until one arrives, use `PMS_GAS_BACKEND=dout`:
this reads the sensor board's on-board comparator through a GPIO pin, which gives
a threshold crossing set by the blue potentiometer, not a magnitude.

That is enough to prove the wiring, the alert path and the fan trigger. It is
**not** enough for the results chapter: `gas_risk_value` can only ever be 0.0 or
1.0, so there is no curve to calibrate and no trend to plot. Order an **ADS1115**
(I²C, 16-bit — the easier of the two) or an **MCP3008** (SPI, 10-bit) and switch
the backend with one environment variable. Nothing else in the code changes.

---

## Pin map

BCM numbering, matching Table 3.9 of the dissertation.

| Signal | BCM | Physical pin | Note |
|---|---|---|---|
| DHT22 DATA | 4 | 7 | pull-up on the breakout |
| Relay IN1 (fan) | 17 | 11 | active-low |
| Relay IN2 (heater) | 27 | 13 | active-low |
| MQ135 DOUT | 22 | 15 | only for the `dout` backend |
| Status LED | 24 | 18 | optional heartbeat |
| ADS1115 SDA / SCL | 2 / 3 | 3 / 5 | I²C backend |
| MCP3008 SPI0 | 10, 9, 11, 8 | 19, 21, 23, 24 | SPI backend |
| 3.3 V | — | 1, 17 | DHT22, ADC, relay logic side |
| 5 V | — | 2, 4 | MQ135 heater, relay coil side |
| GND | — | 6, 9, 14, 20, 25, 30, 34, 39 | must be common to everything |

### Three wiring rules that protect the Pi

1. **Power the DHT22 from 3.3 V, never 5 V.** Its data line idles at the supply
   rail, and a 5 V line on a GPIO pin damages the Pi. The sensor works fine at
   3.3 V.
2. **Never take MQ135 AOUT or DOUT straight to a GPIO pin.** The MQ135's heater
   needs 5 V and both outputs swing to ~5 V. Fit a **10 kΩ / 10 kΩ divider** —
   AOUT to the top, GND to the bottom, the junction to the Pi or ADC — which
   halves it to a safe 2.5 V. `PMS_GAS_DIVIDER_RATIO=2.0` scales the reading back
   up in software.
3. **Split the relay board's supply.** Remove the VCC–JD_VCC jumper, feed JD_VCC
   from 5 V (the coils need it) and VCC from 3.3 V (the logic side). Left jumpered
   at 5 V, a 3.3 V GPIO never rises far enough above the opto-coupler's cathode to
   switch it off, and the channel chatters or sticks on.

---

## Steps

### 0. Prepare the Pi

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv python3-opencv i2c-tools
```

```bash
sudo raspi-config nonint do_i2c 0
```

```bash
sudo raspi-config nonint do_spi 0
```

Then, with the Pi **powered off and unplugged** for every wiring change:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-pi.txt
```

```bash
python3 tools/00_check_pi.py
```

Fix every `FAIL` before wiring anything. A `Power` failure matters more than it
looks: under-voltage silently corrupts DHT22 frames and makes relays chatter.

### 1. DHT22 alone

`VCC → 3.3 V (pin 1)`, `DATA → BCM4 (pin 7)`, `GND → GND (pin 6)`.

```bash
python3 tools/01_test_dht22.py
```

A few failed reads are normal — the DHT22 is bit-banged with no clock line, so
any scheduling hiccup corrupts a frame. Above ~60% success is fine. 0% means
wiring.

### 2. Relays with LEDs

Relay logic side to 3.3 V/GND per rule 3 above, `IN1 → BCM17`, `IN2 → BCM27`.

On the switched side of each channel, wire an LED as the stand-in load:
`3.3 V → COM`, `NO → LED anode`, `LED cathode → 220–470 Ω → GND`.

```bash
python3 tools/02_test_relay.py
```

You should hear each relay click and see its LED follow. If a channel is
inverted, the board is active-high: rerun with `--active-high` and set
`PMS_RELAY_ACTIVE_LOW=false`.

### 3. MQ135

`VCC → 5 V (pin 2)`, `GND → GND`. Then either:

- **No ADC yet:** `DOUT → 10 kΩ/10 kΩ divider → BCM22 (pin 15)`
- **ADS1115:** `AOUT → divider → A0`; ADS1115 `VDD → 3.3 V`, `SDA → pin 3`, `SCL → pin 5`
- **MCP3008:** `AOUT → divider → CH0`; MCP3008 on SPI0, `VDD`/`VREF → 3.3 V`

```bash
python3 tools/03_test_gas.py --backend dout
```

The element needs ~3 minutes from power-on to settle, and a new sensor needs 24 h
of burn-in before its baseline stops drifting. To provoke a response, hold a swab
of ammonia cleaner nearby — the silicone tube in your kit directs the vapour
without soaking the element. Ventilated room; do not breathe it.

### 4. Camera *(when you have one)*

```bash
python3 tools/04_test_camera.py --index 0
```

Until then set `PMS_VISION_ENABLED=false`, or every cycle raises a capture failure
and the alert queue fills with noise that hides real faults.

### 5–6. Calibrate

```bash
python3 tools/05_mq135_baseline.py --backend ads1115 --minutes 10
```

```bash
python3 tools/06_dht22_calibration.py --samples 20
```

These produce the paired data behind the sensor-calibration figure the study
currently carries as a placeholder, and the per-sensor baseline the gas index
depends on. **Baselines are per-sensor** — the MQ135's clean-air resistance varies
by tens of percent between identical parts. Never copy one between units.

### 7. Full unit

```bash
python3 tools/07_bringup_all.py
```

Exercises sensors, control law, relays, the interlock and the durable queue. When
it passes, move to the soldered board and the enclosure, and only then connect the
fan and heat lamp.

### 8. Run against the server

```bash
sudo cp config/edge.env.example /etc/poultry-edge.env && sudo chmod 600 /etc/poultry-edge.env
```

```bash
python3 -m src.main --cycles 3
```

The env file holds the device token, which is why it is `chmod 600`. Set
`PMS_MOCK=false` in it before running. Then install the systemd unit from
`services/poultry-edge.service`.

---

## Siting

Placement changes the readings more than calibration does.

- **DHT22 and MQ135 at bird level**, out of the fan's draught and out of direct
  sun. A sensor in the airflow reports the fan's success, not the birds'
  conditions.
- **Ammonia pools low**, over the litter — mount the gas sensor near the floor,
  not at head height.
- **Camera** high enough for consistent framing, angled to avoid glare.
- **Enclosure** with cable glands; low-voltage and mains compartments separated.

## Troubleshooting

| Symptom | Cause |
|---|---|
| DHT22 never reads | powered from 5 V, wrong pin, or loose jumper |
| DHT22 reads intermittently | normal below ~40% failure; otherwise long/loose leads |
| Relay clicks but the LED doesn't | LED on NC instead of NO, or reversed polarity |
| Relay stuck on | VCC–JD_VCC jumper still fitted — see rule 3 |
| Relay inverted | active-high board; set `PMS_RELAY_ACTIVE_LOW=false` |
| Gas risk pinned at 1.0 | still warming, or baseline set too low |
| Gas risk only 0.0 or 1.0 | expected on the `dout` backend — fit an ADC |
| `i2cdetect` shows nothing at 0x48 | SDA/SCL swapped, or I²C not enabled |
| Rainbow square on screen | under-voltage; the supply is inadequate |
