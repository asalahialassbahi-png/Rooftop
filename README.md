# Rooftop tyre garden: budget pumped drip irrigation (≈ £120)

This waters the 9 tyre planters on the rooftop walkway from the existing water butt. One small 12 V pump runs on a timer and feeds **one main pipe** along the wall. Each tyre takes its own drop tube, and you **set how much water each plant gets** by its number of adjustable drippers and how far their caps are opened. Every tyre is watered at the same time. Only the amount differs.

| What | Where |
|---|---|
| 3D step-by-step build guide (Blender 4.2+) | [`blender/irrigation_guide.blend`](blender/irrigation_guide.blend) |
| Script that generates the .blend (edit the plants and re-run it) | [`blender/build_irrigation_scene.py`](blender/build_irrigation_scene.py) |
| One rendered image per step | [`renders/step_0.png` … `step_8.png`](renders/) |
| Walkthrough video | [`renders/irrigation_walkthrough.mp4`](renders/irrigation_walkthrough.mp4) |
| Later upgrade: a separate schedule per tyre (≈ £185) | [`upgrade-per-plant/`](upgrade-per-plant/README.md) |

### Using the Blender file
Open `irrigation_guide.blend` and press **Space** to play, or drag the timeline. Each step is a named **timeline marker** ("Step 3: One 13 mm main pipe"). Use the Camera view (Numpad 0) to see it as intended. Instructions for each step appear on screen, labels float next to the parts, and parts drop into place in the order you fit them. In step 7 the whole system runs: the pipe glows, every dripper drips at its own rate, and tags above each tyre show its dripper count and jug target.

To change plants or amounts, edit the `TYRES` list at the top of `build_irrigation_scene.py` and re-run it from Blender's *Scripting* tab, or headless:
```
blender -b -P blender/build_irrigation_scene.py -- --save blender/irrigation_guide.blend --stills renders
```

---

## How it works

```
Water butt ── 12 V brushless pump ── anti-siphon tee (top) ── screen filter ── 13 mm main pipe along the wall ── end stop
   │ float switch                      └ 4 mm bleed back into butt                   │   │   │  ... one per tyre
   │                                                                     4 mm connector + on/off tap + micro-tube
   │                                                                           └ 1–3 adjustable drippers on stakes
12 V timer ── float switch ── relay ── pump        (10 W solar panel → charge controller → 12 V 7 Ah battery)
```

| Problem | How this design handles it |
|---|---|
| Gravity alone is too weak (under 0.1 bar) | A pump with 3–5 m head gives 0.3–0.5 bar, plenty for about 15 drippers over 10 m |
| Every plant needs a different amount | Choose 1, 2 or 3 drippers per tyre, then turn each cap until a jug test hits that tyre's target |
| Tyres far from the pump get less water | The 13 mm main pipe barely loses pressure at these flows (≈ 50 L/h in total), so all tyres get the same pressure |
| The butt siphons itself empty after the pump stops (the drippers sit lower than the water level) | An **anti-siphon tee** at the highest point lets air in through a 4 mm bleed tube back into the butt |
| The pump runs dry and burns out | A float switch in series with the relay coil cuts the pump when the butt is nearly empty |
| Drippers clog with grit from the roof | Pump intake strainer, an inline screen filter, and holes punched in the *side* of the pipe |
| Shutting off one tyre (like the empty one) | Each drop has its own 4 mm on/off tap |
| No mains power on the roof | A 10 W panel keeps a 7 Ah battery charged. The pump only runs about 40 min a week |

## Water per tyre (starting point, UK summer)

Timer: **ON 07:00 → OFF 07:10, Mon / Wed / Fri / Sun**. Add an evening run in a heatwave.

| Tyre | Plant | Drippers | Jug target per minute | Per watering |
|---|---|---|---|---|
| T1 | Wildflowers | 1 | 60 ml | 0.6 L |
| T2 | Thrift & grasses | 1 | 60 ml | 0.6 L |
| T3 | Pansies / violas | 2 | 160 ml | 1.6 L |
| T4 | Empty (red saucer) | 1, tap **off** | – | – |
| T5 | Lavender (likes it dry) | 1 | 30 ml | 0.3 L |
| T6 | Geranium + nasturtium | 2 | 100 ml | 1.0 L |
| T7 | Geranium | 2 | 100 ml | 1.0 L |
| T8 | Strawberries | 3 | 300 ml | 3.0 L |
| T9 | Gravel / succulent | 1 | 15 ml (or tap off and water by hand) | 0.15 L |

Each watering uses about 8 L, which is about **33 L a week**. A full 100 L butt lasts about **3 weeks without rain**.

**Setting the amounts (10 minutes, once):** press the timer's MANUAL / ON button so the pump runs. Hold a measuring jug under one tyre's drippers for exactly 1 minute. Turn the caps (open = more) until you hit the target, then move on to the next tyre. Turning one tyre up slightly reduces the others, so do a second quick pass at the end. After a week, push a finger 5 cm into each tyre. If a tyre is soggy, close its caps a little. If it's dry, open them, or add a dripper.

## Parts list (approx. UK prices, Amazon/eBay/AliExpress, 2026)

| # | Part | Qty | ≈ £ |
|---|---|---|---|
| 1 | 12 V **brushless** submersible pump, **3–5 m max head**, 300–800 L/h | 1 | 15 |
| 2 | Vertical float switch (reed type) + cable ties / short rod | 1 | 3 |
| 3 | 12 V automotive relay (30 A) with socket + 2 × 1N4007 diodes | 1 | 3 |
| 4 | **12 V DC** programmable timer switch, 7-day, 1-minute steps (e.g. "CN101A DC12V" type) | 1 | 8 |
| 5 | Inline blade fuse holder + 5 A fuse | 1 | 2 |
| 6 | 12 V 7 Ah sealed lead-acid battery | 1 | 17 |
| 7 | 10 W 12 V solar panel + angle bracket | 1 | 15 |
| 8 | 10 A PWM solar charge controller **with LOAD output** | 1 | 7 |
| 9 | IP65 junction box ~200×150×100 mm + 3 cable glands | 1 | 8 |
| 10 | 2-core cable (~10 m) + Wago 221 connectors | – | 6 |
| 11 | 13 mm LDPE drip main pipe, 15 m | 1 | 8 |
| 12 | 13 mm fittings: 1 tee, 1 end stop, 1 tee-to-4 mm reducer, jubilee clip, inline screen filter | – | 7 |
| 13 | Drip fittings kit: ≥ 20 adjustable drippers on stakes, 4 mm barbed connectors, 4 mm tees, 10 inline 4 mm taps | 1 | 12 |
| 14 | 4/7 mm micro-tube, 20 m | 1 | 5 |
| 15 | Drip-pipe hole punch | 1 | 3 |
| | **Total** | | **≈ £120** |

**Cheaper still:**
* **There's a socket on the roof or near it:** replace parts 6–8 (≈ £39) with a 12 V 2 A mains adapter (≈ £8). That brings the total to **≈ £89**. Keep the adapter indoors or in the box.
* **Skip the inline filter:** pull an old pair of tights over the pump intake instead and save about £4. You'll have to rinse it more often.
* **An all-in-one "solar drip irrigation kit" (≈ £35–50):** this is the cheapest route, but the small pumps in these kits often struggle to push water 10 m to 9 tyres, and you get less control over each plant. If you try one, check it says **≥ 10 outlets** and **adjustable drippers**.

## Build steps (same as the Blender guide)

0. **Remove the old line.** Take down the shared drip line and droppers, and **keep the white wall clips**.
1. **Pump + float switch.** Sit the pump flat on the butt floor. Cable-tie the float switch to a weighted rod about 15 cm above the pump intake. Bring both cables out through a hole in the lid with a grommet.
2. **Solar panel + timer box.** Bolt the panel to the coping, facing roughly south. Fix the IP65 box to the wall with masonry screws, with the cable glands on the bottom and a drip loop on every cable. Inside go the battery, charge controller, timer, relay and fuse.
3. **Main pipe.** Run 13 mm pipe from the pump outlet up over the butt rim. At the **highest point** fit a 13 mm tee, with a 4 mm reducer and a short 4 mm tube running back down into the butt. This is the **anti-siphon bleed**; don't skip it. Fit the screen filter on the way down, then run the pipe along the wall in the existing clips (cable-tie it in). End 30 cm past the last tyre with an end stop.
4. **Drop tubes.** At each tyre, punch a hole in the **side** of the main pipe and push in a 4 mm barbed connector. Then fit a 4 mm on/off tap, then micro-tube down the wall into the tyre.
5. **Drippers.** Fit 1–3 adjustable drippers on stakes per tyre (see the table), joined with 4 mm tees, either side of the plant.
6. **Wiring:**

   | From | To |
   |---|---|
   | Solar panel + / − | Charge controller **PV** |
   | Battery + (through the **5 A fuse**) / − | Charge controller **BAT** |
   | Charge controller **LOAD** + / − | +12 V rail / GND rail |
   | Timer DC+ / DC− | +12 V rail / GND rail |
   | Timer **COM** | +12 V rail |
   | Timer **NO** | float switch → relay **86** |
   | Relay **85** | GND rail |
   | Relay **30** | +12 V rail |
   | Relay **87** | pump + (pump − to GND rail) |
   | 1N4007 diode across relay 85/86 and across the pump | **band (stripe) to the + side** |

   Connect the battery to the controller **before** the panel, which is what most PWM controllers want.
7. **Timer + amounts.** Set the clock, then the program: ON 07:00, OFF 07:10, Mon/Wed/Fri/Sun. Run the jug test above. Check every joint for drips while it runs.
8. **Maintenance.** Weekly, glance at the butt level. Monthly, rinse the filter and flick each dripper cap open and shut to clear grit. Before frost, lift the pump, drain the pipe and keep the battery indoors and charged.

### Notes
* A full 100 L butt weighs about 100 kg, the same as it does today. The new parts add only a few kg.
* Tyres can leach compounds into the soil. Many people line the inside of tyres used for edible plants (the strawberries) with a heavy plastic sheet.
* Want separate days for different plants later? [`upgrade-per-plant/`](upgrade-per-plant/README.md) adds valves and a small controller on top of this build.
