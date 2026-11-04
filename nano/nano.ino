#include <ArduinoJson.h>
#include <SoftwareSerial.h>
SoftwareSerial esp32(3, 4);

int delayctr = 5;

#define voltpin A6
#define relaypin A5
#define irpin A4

unsigned long previousMillis = 0;
int ctr = 0;

float receivedData;
float adc_voltage = 0.0;
float in_voltage = 0.0;

// Floats for resistor values in divider (in ohms)
float R1 = 30000.0;
float R2 = 7500.0;

// Float for Reference Voltage
float ref_voltage = 5.0;

// Calibration: adjust so the printed voltage matches the real battery voltage.
// Door 1: CAL = 1.00   Door 2: CAL = 3.7385   (edit the one for the Nano you're flashing)
float CAL = 0.94;

// Battery curve (resting voltage -> percent). Example: 3S LiPo. Edit for your pack.
const float PACK_V[] = { 10.50, 10.95, 11.25, 11.55, 12.00, 12.60 };
const int PACK_P[] = { 0, 10, 30, 55, 78, 100 };
const int PACK_N = 6;

int batteryPercent(float v) {
  if (v <= PACK_V[0]) return 0;
  if (v >= PACK_V[PACK_N - 1]) return 100;
  for (int i = 1; i < PACK_N; i++) {
    if (v <= PACK_V[i]) {
      float t = (v - PACK_V[i - 1]) / (PACK_V[i] - PACK_V[i - 1]);
      return (int)(PACK_P[i - 1] + t * (PACK_P[i] - PACK_P[i - 1]) + 0.5);
    }
  }
  return 100;
}

// Integer for ADC value
int adc_value = 0;

int status = 0;

void setup() {
  Serial.begin(115200);
  esp32.begin(9600);

  pinMode(irpin, INPUT_PULLUP);
  pinMode(relaypin, OUTPUT);
  digitalWrite(relaypin, HIGH);
}

void loop() {

  if (esp32.available()) {
    receivedData = esp32.parseInt();
    Serial.print("Received data: ");
    Serial.println(receivedData);
    if (receivedData == 1) {
      digitalWrite(relaypin, LOW);
      delay(1000);
      digitalWrite(relaypin, HIGH);
    }
  }

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= 1000) {
    previousMillis = currentMillis;

    // Average 16 readings to smooth out noise
    long adc_sum = 0;
    for (int i = 0; i < 16; i++) {
      adc_sum += analogRead(voltpin);
      delay(2);
    }
    adc_value = adc_sum / 16;
    adc_voltage = (adc_value * ref_voltage) / 1024.0;
    in_voltage = adc_voltage * (R1 + R2) / R2 * CAL;
    Serial.print("Input Voltage = ");
    Serial.println(in_voltage, 2);
    int mappedValue = batteryPercent(in_voltage);

    if (digitalRead(irpin) == LOW) {
      ctr++;
      Serial.print("DETECTION COUNTER : ");
      Serial.println(ctr);
      if (ctr >= delayctr) {
        Serial.println("DETECTION FOUND !!");
        status = 1;
      }
    } else {
      Serial.println("NO DETECTION !!");
      ctr = 0;
      status = 0;
    }
    Serial.println(mappedValue);
    esp32.print(mappedValue);
    esp32.print(",");
    esp32.println(status);
  }
}