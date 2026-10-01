/*
  Rooftop tyre-garden irrigation controller
  -----------------------------------------
  ESP32 DevKit (WROOM) + DS3231 RTC + 10 logic-level MOSFET modules
  9 x 12 V normally-closed solenoid valves (one per tyre) + 12 V submersible pump.

  Every WAKE_MINUTES the ESP32 wakes from deep sleep, reads the clock and waters
  any tyre whose own interval has elapsed, ONE TYRE AT A TIME (so every tyre gets
  full pump pressure and the run time = volume / dripper flow is predictable).

  Safety:
    * Float switch: pump never runs if the butt is nearly empty (no dry running).
    * Battery check: skips watering below BATT_MIN_V (charge controller LVD backs this up).
    * Per-valve run-time cap (MAX_RUN_SECONDS) in case of a typo in the schedule.
    * Valves are normally-closed: a crash / power loss = everything shut, no siphoning.
    * All outputs are driven LOW and held LOW during deep sleep.

  Test / calibration: press the button on the box. Every tyre (even ones set to 0)
  runs TEST_SECONDS in order T1..T9. Catch one dripper pair in a jug:
      L/h for that tyre = millilitres collected * 3600 / (TEST_SECONDS * 1000)
  Put the result in DRIP_LPH[] below, or adjust the dripper caps until it reads ~20.

  Libraries: "RTClib" by Adafruit (Library Manager). Board: "ESP32 Dev Module".
*/

#include <Wire.h>
#include <RTClib.h>
#include <Preferences.h>
#include "driver/gpio.h"
#include "driver/rtc_io.h"

// ---------------------------------------------------------------- schedule
// T1 is the tyre nearest the water butt. everyDays = 0 switches a tyre off.
struct Tyre {
  const char *name;
  uint8_t pin;        // ESP32 GPIO driving that valve's MOSFET module
  uint8_t everyDays;  // 1 = daily, 2 = every other day, ...
  float litres;       // water per session
};

Tyre TYRES[] = {
  {"T1 Wildflowers",      4, 3, 0.8},
  {"T2 Thrift & grass",  13, 3, 0.8},
  {"T3 Pansies",         16, 1, 0.8},
  {"T4 Empty / new",     17, 0, 0.0},
  {"T5 Lavender",        18, 4, 0.6},
  {"T6 Geranium+nast.",  19, 2, 1.0},
  {"T7 Geranium",        23, 2, 1.0},
  {"T8 Strawberries",    25, 1, 1.5},
  {"T9 Gravel/succulent",26, 7, 0.4},
};
const int N_TYRES = sizeof(TYRES) / sizeof(TYRES[0]);

// Measured flow of each tyre's dripper pair (litres per hour). See calibration above.
float DRIP_LPH[N_TYRES] = {20, 20, 20, 20, 20, 20, 20, 20, 20};

const uint8_t WATER_HOUR = 6;     // earliest time watering may start (RTC local time)
const uint8_t WATER_MINUTE = 30;
const uint8_t LAST_HOUR = 20;     // catch-up window: missed sessions may run until 20:00
const uint8_t WAKE_MINUTES = 15;  // how often to wake and check
const uint16_t MAX_RUN_SECONDS = 15 * 60;
const uint16_t TEST_SECONDS = 60;
const uint8_t PRIME_SECONDS = 3;  // pump runs this long before the first valve opens

// ---------------------------------------------------------------- pins
const uint8_t PUMP_PIN = 27;
const uint8_t FLOAT_PIN = 32;      // float switch to GND
const uint8_t BUTTON_PIN = 33;     // test button to GND (also wakes from sleep)
const uint8_t BATT_PIN = 34;       // 100k (to +12 V) / 27k (to GND) divider
const uint8_t LED_PIN = 2;         // on-board LED (+ optional panel LED via 330R)
const int FLOAT_OK_LEVEL = LOW;    // LOW = contacts closed = water above the float.
                                   // If yours reads the other way, flip the float or set HIGH.
const bool USE_BATTERY_CHECK = true;
const float BATT_DIVIDER = (100.0 + 27.0) / 27.0;
const float BATT_MIN_V = 11.6;

RTC_DS3231 rtc;
Preferences prefs;

// ---------------------------------------------------------------- helpers
void allOff() {
  for (int i = 0; i < N_TYRES; i++) digitalWrite(TYRES[i].pin, LOW);
  digitalWrite(PUMP_PIN, LOW);
}

bool waterOk() { return digitalRead(FLOAT_PIN) == FLOAT_OK_LEVEL; }

float batteryVolts() {
  uint32_t mv = 0;
  for (int i = 0; i < 16; i++) mv += analogReadMilliVolts(BATT_PIN);
  return (mv / 16.0) / 1000.0 * BATT_DIVIDER;
}

bool batteryOk() {
  if (!USE_BATTERY_CHECK) return true;
  float v = batteryVolts();
  Serial.printf("Battery %.2f V\n", v);
  return v >= BATT_MIN_V;
}

// Open one valve for `seconds` with the pump running. Returns false if the butt ran dry.
bool runValve(int i, uint32_t seconds) {
  if (seconds > MAX_RUN_SECONDS) seconds = MAX_RUN_SECONDS;
  Serial.printf("  %s: %lu s\n", TYRES[i].name, (unsigned long)seconds);
  digitalWrite(TYRES[i].pin, HIGH);
  bool ok = true;
  for (uint32_t s = 0; s < seconds; s++) {
    if (!waterOk()) { ok = false; break; }
    digitalWrite(LED_PIN, s & 1);
    delay(1000);
  }
  digitalWrite(TYRES[i].pin, LOW);
  digitalWrite(LED_PIN, LOW);
  delay(500);  // let the valve close before opening the next one
  return ok;
}

void pumpOn() {
  digitalWrite(PUMP_PIN, HIGH);
  delay(PRIME_SECONDS * 1000UL);
}

uint32_t secondsFor(int i) {
  if (DRIP_LPH[i] <= 0) return 0;
  return (uint32_t)(TYRES[i].litres / DRIP_LPH[i] * 3600.0 + 0.5);
}

// ---------------------------------------------------------------- modes
void testRun() {
  Serial.println("TEST RUN: every tyre in turn");
  if (!waterOk()) { Serial.println("Butt too low - refusing to run pump"); return; }
  pumpOn();
  for (int i = 0; i < N_TYRES; i++) {
    if (!runValve(i, TEST_SECONDS)) { Serial.println("Butt ran low - stopping"); break; }
  }
  allOff();
}

void scheduledRun(const DateTime &now) {
  int32_t today = now.unixtime() / 86400L;
  int minutes = now.hour() * 60 + now.minute();
  if (minutes < WATER_HOUR * 60 + WATER_MINUTE || now.hour() >= LAST_HOUR) return;

  bool due[N_TYRES];
  bool anyDue = false;
  prefs.begin("irrig", false);
  for (int i = 0; i < N_TYRES; i++) {
    char key[4];
    snprintf(key, sizeof key, "d%d", i);
    int32_t last = prefs.getInt(key, 0);
    due[i] = TYRES[i].everyDays > 0 && TYRES[i].litres > 0 && (today - last) >= TYRES[i].everyDays;
    anyDue |= due[i];
  }
  if (!anyDue) { prefs.end(); return; }

  Serial.printf("%04d-%02d-%02d %02d:%02d watering\n", now.year(), now.month(), now.day(), now.hour(), now.minute());
  if (!waterOk()) { Serial.println("Butt too low - skipping"); prefs.end(); return; }
  if (!batteryOk()) { Serial.println("Battery low - skipping"); prefs.end(); return; }

  pumpOn();
  for (int i = 0; i < N_TYRES; i++) {
    if (!due[i]) continue;
    if (!runValve(i, secondsFor(i))) { Serial.println("Butt ran low - stopping"); break; }
    char key[4];
    snprintf(key, sizeof key, "d%d", i);
    prefs.putInt(key, today);  // only marked done once it has actually been watered
  }
  allOff();
  prefs.end();
}

void goToSleep() {
  allOff();
  for (int i = 0; i < N_TYRES; i++) gpio_hold_en((gpio_num_t)TYRES[i].pin);
  gpio_hold_en((gpio_num_t)PUMP_PIN);
  gpio_deep_sleep_hold_en();
  rtc_gpio_pullup_en(GPIO_NUM_33);
  rtc_gpio_pulldown_dis(GPIO_NUM_33);
  esp_sleep_enable_ext0_wakeup(GPIO_NUM_33, 0);
  esp_sleep_enable_timer_wakeup((uint64_t)WAKE_MINUTES * 60ULL * 1000000ULL);
  Serial.flush();
  esp_deep_sleep_start();
}

// ---------------------------------------------------------------- main
void setup() {
  // Release the sleep holds before touching the outputs
  for (int i = 0; i < N_TYRES; i++) gpio_hold_dis((gpio_num_t)TYRES[i].pin);
  gpio_hold_dis((gpio_num_t)PUMP_PIN);
  for (int i = 0; i < N_TYRES; i++) pinMode(TYRES[i].pin, OUTPUT);
  pinMode(PUMP_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  allOff();
  pinMode(FLOAT_PIN, INPUT_PULLUP);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  Serial.begin(115200);
  delay(50);
  Wire.begin(21, 22);
  if (!rtc.begin()) {
    Serial.println("DS3231 not found - check SDA 21 / SCL 22. Sleeping.");
    goToSleep();
  }
  if (rtc.lostPower()) {
    // First boot or flat coin cell: set the clock to the time this sketch was compiled.
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    Serial.println("RTC time set from compile time");
  }

  if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_EXT0) {
    testRun();
  } else {
    scheduledRun(rtc.now());
  }
  goToSleep();
}

void loop() {}
