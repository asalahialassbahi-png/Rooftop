# Upgrade option: a separate schedule for every tyre (≈ £185)

> **This is not the recommended build.** The budget build in the [main README](../README.md) (≈ £120) waters all tyres together and varies the *amount* per plant. Use this version only if you later want each tyre on its **own interval** (for example, strawberries daily and lavender every 4 days). It reuses the budget build's pump, float switch, solar power and drippers. It adds 9 valves, an ESP32 controller and separate tubes.

| What | Where |
|---|---|
| Script that builds the per-plant 3D guide (Blender 4.2+) | [`build_irrigation_scene_per_plant.py`](build_irrigation_scene_per_plant.py) |
| ESP32 controller firmware | [`firmware/rooftop_irrigation/rooftop_irrigation.ino`](firmware/rooftop_irrigation/rooftop_irrigation.ino) |

To see the per-plant 3D guide, generate it (it isn't stored as a .blend file):
```
blender -b -P upgrade-per-plant/build_irrigation_scene_per_plant.py -- --save per_plant_guide.blend
```

---

## Why the old setup can't do per-plant watering

* **One shared line** means every tyre is watered at the same moment for the same length of time. The only way to vary it is by guessing at dripper sizes.
* **Gravity pressure is tiny.** A 1 m tall butt standing on the same roof as the tyres gives under 0.1 bar. Most battery hose timers and almost all solenoid valves need at least 0.2 bar to open properly, so a gravity system with timer valves floods some tyres and starves others.

## The design

```
Water butt ── 12 V brushless pump (5 m head ≈ 0.45 bar) ── screen filter ── manifold
                                                                              │
             ┌──────────── 9 × 12 V normally-closed solenoid valves ──────────┘
             │  (one per tyre, opened ONE AT A TIME by the ESP32)
             └─ 9 separate 4/7 mm micro-tubes in the existing wall clips
                   └─ at each tyre: tee → 2 adjustable drippers on stakes
ESP32 + DS3231 clock, powered by a 10 W solar panel → PWM charge controller → 12 V 7 Ah battery
```

How this design avoids the usual failure points:

| Risk | How it is handled |
|---|---|
| Not enough pressure to open the valves | The pump gives about 0.45 bar. The valves need 0.2 bar, so buy ones rated **0.02 MPa minimum**. |
| Pump runs against closed valves | A brushless centrifugal pump can run against a closed valve without damage. |
| Some tyres get more water than others | Only one valve is open at a time, so each tyre gets the full pressure and runs for a predictable time. |
| Pump burns out when the butt is empty | A float switch stops the pump, and the firmware checks it every second. |
| The butt siphons out onto the roof | The valves are **normally closed**. If power is lost or anything crashes, everything shuts. |
| Drippers clog with grit from rainwater | Screen filter after the pump, plus a pump intake strainer. |
| Flat battery | The charge controller's LOAD output has a low-voltage cut-off, and the firmware also skips watering below 11.6 V. |
| No mains power on the roof | Daily use is about 2–3 Wh (pump about 5 min/day plus the ESP32 in deep sleep). A 10 W panel covers this easily, and the battery alone lasts weeks. |

## Plant schedule (from the photos; T1 is nearest the butt)

| Tyre | Plant | Every | Litres | Run time at 20 L/h |
|---|---|---|---|---|
| T1 | Wildflowers | 3 days | 0.8 | 2.4 min |
| T2 | Thrift & grasses | 3 days | 0.8 | 2.4 min |
| T3 | Pansies / violas | daily | 0.8 | 2.4 min |
| T4 | Empty (red saucer) | off | – | – |
| T5 | Lavender (likes it dry) | 4 days | 0.6 | 1.8 min |
| T6 | Geranium + nasturtium | 2 days | 1.0 | 3.0 min |
| T7 | Geranium | 2 days | 1.0 | 3.0 min |
| T8 | Strawberries | daily | 1.5 | 4.5 min |
| T9 | Gravel / succulent | 7 days | 0.4 | 1.2 min |

That averages about **4 L/day**, so a full 100 L butt lasts about **3 weeks without rain**. These numbers are a starting point for a UK summer. Check the soil 5 cm down after a week, then change `everyDays` / `litres` in the firmware.

## Parts list (approx. UK prices, Amazon/eBay/AliExpress, 2026)

| # | Part | Qty | ≈ £ |
|---|---|---|---|
| 1 | 12 V **brushless** submersible pump, ≥5 m max head, ~500 L/h (e.g. "DC40-1250" type) | 1 | 15 |
| 2 | Vertical float switch (reed type) + short stainless rod / cable ties | 1 | 3 |
| 3 | 12 V DC **normally-closed** 1/2" BSP plastic solenoid valve, **0.02–0.8 MPa** | 9 | 32 |
| 4 | 1/2" BSP female PP tees ×9, 1/2" hex nipples ×9, end cap, 1/2" × 13 mm hose-tail, PTFE tape | – | 12 |
| 5 | Inline screen filter, 13 mm | 1 | 4 |
| 6 | 13 mm hose 2 m + 2 jubilee clips | 1 | 5 |
| 7 | 1/2" BSP female → 4/7 mm barbed adaptor | 9 | 5 |
| 8 | 4/7 mm black micro-tube, **50 m** roll (the 9 runs add up to about 45 m) | 1 | 10 |
| 9 | Adjustable 0–70 L/h drippers on stakes ×20, 4 mm tees ×10 | – | 7 |
| 10 | ESP32 DevKit V1 (WROOM-32) | 1 | 7 |
| 11 | DS3231 RTC module + CR2032 | 1 | 3 |
| 12 | Logic-level MOSFET trigger modules (AOD4184 / "D4184", work from 3.3 V) | 10 | 8 |
| 13 | 1N5819 (or 1N4007) diodes, 100 kΩ + 27 kΩ resistors | 10 + 2 | 1 |
| 14 | 12 V → 5 V buck converter (mini-360 / LM2596) | 1 | 3 |
| 15 | IP65 enclosure ~300×250×120 mm + 4 cable glands | 1 | 15 |
| 16 | IP67 momentary push button 16 mm | 1 | 3 |
| 17 | 10 W 12 V solar panel + angle bracket | 1 | 15 |
| 18 | 10 A PWM solar charge controller **with LOAD output** | 1 | 7 |
| 19 | 12 V 7 Ah sealed lead-acid battery | 1 | 17 |
| 20 | Inline blade fuse holder + 5 A fuse | 1 | 2 |
| 21 | 2-core cable (1 mm² 5 m for pump/panel, 0.5 mm² for valves), Wago 221 connectors | – | 12 |
| | **Total** | | **≈ £185** |

**Ways to cut the cost:**
* **Group tyres on the same schedule.** For example, T3+T8 daily, T6+T7 every 2 days, and T1+T2 every 3 days. That needs 5 valves and 6 modules instead of 9 and 10, saving about £20. In the firmware, give tyres in a group the same `pin`. They will then run together, so set the drippers to share the volume.
* **Skip solar.** Do this if there's an outdoor socket, or if you're happy to take the battery home to charge every few weeks (about 2–3 Wh/day from 84 Wh). That saves about £22.
* **Cheapest possible (~£45)**, but **not** per-plant intervals: a battery *ball-valve* tap timer that works at zero pressure on the butt tap, gravity-fed, with adjustable drippers set per tyre. Every tyre waters at the same time, and only the volume differs.

## Build steps (same as the Blender guide)

0. **Remove the old line.** Take down the shared drip line and droppers, and **keep the white wall clips**.
1. **Pump + float.** Sit the pump flat on the butt floor. Cable-tie the float switch to a weighted rod about 15 cm above the intake. Bring the 13 mm hose and both cables out through a hole in the lid with a grommet.
2. **Solar.** Bolt the panel to the coping on an angle bracket, facing roughly south. Wire it: panel → controller PV, battery → controller BAT with the 5 A fuse on +. Everything else runs from **LOAD**.
3. **Enclosure.** Fix it to the wall with 4 masonry screws and plugs, above the manifold and below the coping. Put the cable glands on the **bottom only**, add a drip loop on every cable, and mount the test button on the front.
4. **Manifold.** Chain the tees with hex nipples, using PTFE tape on every thread. Screw one valve into each tee with the **arrow pointing away from the manifold**. Connect pump hose → filter → manifold inlet, put the end cap on the far end, and fit a 1/2" → 4 mm barb adaptor on each valve outlet. The valve nearest the tyres feeds T1; the one nearest the butt feeds T9.
5. **Tubes.** Run one micro-tube per tyre along the wall in the existing clips. **Tape-label both ends** (T1…T9) before cutting. Don't make any joins along the run. Each tube drops down the wall at its own tyre.
6. **Drippers.** At each tyre fit a 4 mm tee with two short tails and two adjustable drippers on stakes, one each side of the plant. Fit them in the empty tyre too, and leave it `0` in the schedule.
7. **Wiring** (see the step 7 board in Blender):

   | From | To |
   |---|---|
   | Controller LOAD + / − | +12 V rail / GND rail |
   | +12 V rail | each valve's + wire and pump + |
   | each valve − / pump − | its MOSFET module **OUT−** (module VIN+/− to rails) |
   | 1N5819 across every valve and the pump | **band (stripe) to +12 V** |
   | Buck in ← rails; buck 5 V out | ESP32 **VIN** + GND (set the buck to 5.0 V **before** connecting) |
   | DS3231 VCC/GND/SDA/SCL | ESP32 3V3 / GND / **GPIO21** / **GPIO22** |
   | Module TRIG for T1…T9 | GPIO **4, 13, 16, 17, 18, 19, 23, 25, 26** |
   | Module TRIG for pump | GPIO **27** |
   | Float switch | GPIO **32** ↔ GND |
   | Test button | GPIO **33** ↔ GND |
   | +12 V → 100 kΩ → **GPIO34** → 27 kΩ → GND | battery voltage sense |
   | Status LED (optional) | GPIO 2 → 330 Ω → LED → GND |

8. **Program, calibrate, test.**
   * In the Arduino IDE, install the *esp32* boards package and the *RTClib* library. Select board *ESP32 Dev Module* and upload `firmware/rooftop_irrigation/rooftop_irrigation.ino`. The clock sets itself to the upload time on first boot.
   * Press the test button. Each tyre runs for 60 s in turn. Catch one tyre's two drippers in a jug: **ml × 0.06 = L/h**. Adjust the dripper caps until each tyre reads about 20 L/h, or enter the measured value in `DRIP_LPH[]`.
   * Check every joint for drips while it runs.
   * After that it wakes every 15 min. From 06:30 it waters each due tyre one at a time, then goes back to sleep. A session missed because of low water or a low battery is caught up the same day, up to 20:00.

9. **Maintenance.** Weekly, glance at the butt level. Monthly, rinse the screen filter and flick each dripper cap open and shut. Before frost, lift the pump, drain the manifold and valves, and bring the battery inside to keep it charged.

### Notes
* The firmware is syntax-checked but has not been run on hardware. The first test-button run is the real check, so do it before you leave it running unattended.
* Check the tyre weight on the roof. A full 100 L butt is about 100 kg on one spot, which is the same as it is today.
* Tyres can leach compounds into the soil. Many people line the inside of tyres used for edible plants (the strawberries) with a heavy plastic sheet.
