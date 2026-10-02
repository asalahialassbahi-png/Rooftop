# Rooftop tyre garden: low-cost pumped drip irrigation (≈ £62)

This waters the 9 tyre planters on the rooftop walkway from the existing water butt, built for a college with a tight budget. A small 12 V pump runs on a timer and feeds **one main pipe** along the wall. Each tyre has its own drop tube, and you **set how much water each plant gets** with its number of adjustable drippers and how far their caps are opened. Every tyre is watered at the same time. Only the amount differs.

| What | Where |
|---|---|
| 3D step-by-step build guide (Blender 4.2+) | [`blender/irrigation_guide.blend`](blender/irrigation_guide.blend) |
| Script that generates the .blend (edit the plants and re-run it) | [`blender/build_irrigation_scene.py`](blender/build_irrigation_scene.py) |
| One rendered image per step | [`renders/step_0.png` … `step_8.png`](renders/) |
| Walkthrough video | [`renders/irrigation_walkthrough.mp4`](renders/irrigation_walkthrough.mp4) |
| Later upgrade: a separate schedule per tyre (≈ £185) | [`upgrade-per-plant/`](upgrade-per-plant/README.md) |

### Using the Blender file
Open `irrigation_guide.blend` and press **Space** to play, or drag the timeline. Each step is a named **timeline marker**. Use the Camera view (Numpad 0) to see it as intended. Instructions for each step appear on screen, labels float next to the parts, and parts drop into place in the order you fit them. In step 7 the system runs: the pipe glows, every dripper drips at its own rate, and tags above each tyre show its dripper count and jug target.

To change plants or amounts, edit the `TYRES` list at the top of `build_irrigation_scene.py`, then re-run it from Blender's *Scripting* tab, or headless:
```
blender -b -P blender/build_irrigation_scene.py -- --save blender/irrigation_guide.blend --stills renders
```

---

## How it works

```
Water butt ── small 12 V pump (old tights over intake) ── 1 mm anti-siphon hole ── 13 mm main pipe along the wall ── end stop
   │ float switch                                                                   │   │   │  ... one per tyre
   │                                                                  4 mm connector + micro-tube into the tyre
   │                                                                        └ 1–3 adjustable drippers on stakes
12 V weekly timer ── float switch ── pump          (5 W solar panel → charge controller → 12 V 2.3 Ah battery)
```

| Problem | How it is handled |
|---|---|
| Gravity alone is too weak (under 0.1 bar) | A small pump with 3 m head gives roughly 0.2 bar at the tyres, enough for adjustable drippers |
| Every plant needs a different amount | Fit 1, 2 or 3 drippers per tyre, then turn each cap until a jug test hits that tyre's target |
| Tyres far from the pump get less | The 13 mm main pipe barely loses pressure at about 50 L/h, so every tyre gets the same pressure |
| The butt siphons itself empty after the pump stops (the drippers are lower than the water) | A **1 mm hole** in the pipe just under the butt lid lets air in when the pump stops. While pumping it only squirts a little back into the butt |
| The pump runs dry and burns out | A float switch wired **in series** with the pump cuts it when the butt is nearly empty |
| Drippers clog with grit | Old tights over the pump intake, and holes made in the *side* of the pipe |
| Turning a tyre off (like the empty one) | Screw its adjustable dripper caps fully shut |
| No mains power on the roof | The pump uses under 5 W for about 40 min a week. A 5 W panel keeps a small battery topped up |

## Water per tyre (starting point, UK summer)

Timer: **ON 07:00 → OFF 07:10, Mon / Wed / Fri / Sun**. Add an evening run in a heatwave.

| Tyre | Plant | Drippers | Jug target per minute | Per watering |
|---|---|---|---|---|
| T1 | Wildflowers | 1 | 60 ml | 0.6 L |
| T2 | Thrift & grasses | 1 | 60 ml | 0.6 L |
| T3 | Pansies / violas | 2 | 160 ml | 1.6 L |
| T4 | Empty (red saucer) | 1, caps **closed** | – | – |
| T5 | Lavender (likes it dry) | 1 | 30 ml | 0.3 L |
| T6 | Geranium + nasturtium | 2 | 100 ml | 1.0 L |
| T7 | Geranium | 2 | 100 ml | 1.0 L |
| T8 | Strawberries | 3 | 300 ml | 3.0 L |
| T9 | Gravel / succulent | 1 | 15 ml (or caps closed, water by hand) | 0.15 L |

Each watering uses about 8 L, which is about **33 L a week**. A full 100 L butt lasts about **3 weeks without rain**.

**Setting the amounts (once, about 10 minutes):** press the timer's MANUAL / ON button so the pump runs. Hold a measuring jug under one tyre's drippers for exactly 1 minute. Turn the caps (open = more) until you hit the target, then move on to the next tyre. Do a second quick pass at the end, because opening one tyre slightly reduces the others. If the small pump can't reach the strawberries' 300 ml, set the timer to 15 minutes and aim for ⅔ of every target. After a week, push a finger 5 cm into each tyre. If a tyre is soggy, close its caps a little; if it's dry, open them or add a dripper.

## Parts list (approx. UK prices for the cheapest reliable versions, 2026; AliExpress is usually cheapest, Amazon/eBay a little more)

| # | Part | Qty | ≈ £ |
|---|---|---|---|
| 1 | 12 V DC **brushless** submersible pump, **3 m max head**, **under 5 W / 0.4 A** (often sold as "12 V 240 L/h") | 1 | 7 |
| 2 | Vertical float switch, reed type (rated ~10 W / 0.5 A) | 1 | 2 |
| 3 | **12 V DC** weekly programmable timer switch, 1-minute steps (e.g. "CN101A DC12V" type) | 1 | 6 |
| 4 | 12 V 2.3 Ah sealed lead-acid battery | 1 | 10 |
| 5 | 5 W 12 V solar panel | 1 | 9 |
| 6 | Small PWM solar charge controller **with LOAD output** | 1 | 6 |
| 7 | Inline fuse holder + 3 A fuse | 1 | 1.50 |
| 8 | Lidded plastic storage box (pound shop) | 1 | 2 |
| 9 | 2-core cable ~5 m + a strip of screw terminals | – | 3 |
| 10 | 13 mm LDPE drip main pipe, 15 m | 1 | 6 |
| 11 | 13 mm end stop + cable ties | – | 1.50 |
| 12 | 4/7 mm micro-tube, 15 m | 1 | 3 |
| 13 | Adjustable drippers on stakes ×20, 4 mm barbed connectors ×10, 4 mm tees ×10 (sold as one bag) | – | 5 |
| | **Total** | | **≈ £62** |

**Free / borrowed:** old tights (filter), a hot needle or 1 mm drill bit (anti-siphon hole), a hot nail, bradawl or 3 mm drill (pipe holes, so no punch tool needed), the existing white wall clips, masonry screws and cable ties from the site team.

### What was cut from the ≈ £120 version, and why it still works

| Cut | Saved | Why it's safe |
|---|---|---|
| 15 W pump → **< 5 W pump** (3 m head) | £8 | The lift is only about 1.2 m. 3 m head still leaves about 0.2 bar for the drippers |
| Car relay + diodes | £3 | The < 0.4 A pump goes **straight through the float switch**, which is rated about 0.5 A |
| 7 Ah battery → **2.3 Ah**, 10 W panel → **5 W**, cheaper controller | £14 | The pump only uses about 3 Wh a week. A 2.3 Ah battery runs the timer for days of cloud |
| IP65 enclosure → **lidded plastic box**, holes in the bottom only | £6 | Sealed battery, and the box sits under the coping out of direct rain |
| Inline screen filter → **old tights** over the intake | £4 | Same job; rinse it monthly |
| Anti-siphon tee + reducer → **1 mm hole** in the pipe | £1.50 | Same job, a standard trick in pond and aquarium pumps |
| 9 inline taps → **close the dripper caps** | £3 | Adjustable drippers shut off fully |
| Hole-punch tool → hot nail / bradawl | £3 | The 4 mm barbed connectors still seal |
| Cheapest sources for the timer, float, fuse, cable, pipe, tube and drippers | £14.50 | Same parts, bought as AliExpress-style bags instead of branded packs |
| **Total saved** | **≈ £57** | **≈ £119 → ≈ £62** |

### Even cheaper, if possible
* **Reuse the existing drip line.** Measure the black line already on the wall. If it's 13 mm or wider (about 16 mm outside), keep it and its droppers. That saves parts 10–12 (≈ £10), bringing the total to **≈ £52**.
* **A socket the site team can provide** (RCD-protected, weatherproof, fitted by a qualified person): replace parts 4–6 (≈ £25) with a 12 V 1 A mains adapter (≈ £5) kept indoors or in the box. That brings the total to **≈ £42**.
* **Ask the D&T, physics or engineering department first.** Batteries, panels, fuses, cable, boxes and screw terminals are often already in a store cupboard.

## Build steps (same as the Blender guide)

0. **Prepare.** Remove the old line and droppers, unless you're reusing them (see above). **Keep the white wall clips.**
1. **Pump + float switch.** Pull old tights over the pump intake and cable-tie them. Sit the pump flat on the butt floor. Cable-tie the float switch to a weighted rod about 15 cm above the intake. Bring the cables out through a hole in the lid.
2. **Solar panel + box.** Fix the panel on the coping, tilted to face roughly south. Screw the plastic box to the wall under the coping, and drill its cable holes in the **bottom only**. Inside go the battery, controller, timer and fuse.
3. **Main pipe.** Run 13 mm pipe from the pump up through the lid and over the rim. **Just under the lid, make a 1 mm hole** in the pipe, above the highest the water ever gets. This is the anti-siphon hole; don't skip it. Run the pipe along the wall in the clips with cable ties, 30 cm past the last tyre, and fit the end stop.
4. **Drop tubes.** At each tyre, make a hole in the **side** of the main pipe (hot nail or 3 mm drill) and push in a 4 mm barbed connector. Run micro-tube down the wall into the tyre.
5. **Drippers.** Fit 1–3 adjustable drippers on stakes per tyre (see the table), joined with 4 mm tees, either side of the plant.
6. **Wiring (5 connections, no relay):**

   | From | To |
   |---|---|
   | Solar panel + / − | Charge controller **PV** |
   | Battery + (through the **3 A fuse**) / − | Charge controller **BAT** (connect this **before** the panel) |
   | Charge controller **LOAD** + / − | Timer DC+ / DC− |
   | Timer **COM** | LOAD + |
   | Timer **NO** → float switch → pump + | pump − to LOAD − |

   This only works because the pump draws **under 0.4 A**. Check the pump's label: if it says more than 5 W, add a 12 V car relay (≈ £3) so the float switch only switches the relay coil.
7. **Timer + amounts.** Set the clock, then the program: ON 07:00, OFF 07:10, Mon/Wed/Fri/Sun. Run the jug test above. Check every joint for drips while it runs.
8. **Maintenance.** Weekly, glance at the butt level. Monthly, rinse the tights filter and flick each dripper cap open and shut to clear grit. Before frost, lift the pump, drain the pipe and keep the battery indoors and charged.

### Notes
* Check with the college site / estates team before fixing anything to the roof or walls. They may also supply screws, cable ties and cable for free.
* Tyres can leach compounds into the soil. Many people line the inside of tyres used for edible plants (the strawberries) with a heavy plastic sheet.
* Want separate days for different plants later? [`upgrade-per-plant/`](upgrade-per-plant/README.md) shows a valve-and-controller version.
