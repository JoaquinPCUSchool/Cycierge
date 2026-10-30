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

// Integer for ADC value
int adc_value = 0;

int status = 0;

void setup() {
  Serial.begin(115200);
  esp32.begin(9600);

  pinMode(irpin, INPUT_PULLUP);
  pinMode(relaypin, OUTPUT); digitalWrite(relaypin, HIGH);


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
   
    adc_value = analogRead(voltpin);
    adc_voltage  = (adc_value * ref_voltage) / 1024.0;
    in_voltage = adc_voltage * (R1 + R2) / R2;
    Serial.print("Input Voltage = ");
    Serial.println(in_voltage, 2);
    int mappedValue = map(in_voltage, 11.5, 12.7, 0, 100);
    

    if (digitalRead(irpin) == LOW) {
      ctr ++;
      Serial.print("DETECTION COUNTER : "); Serial.println(ctr);
      if (ctr >= delayctr) {
        Serial.println("DETECTION FOUND !!");
        status = 1;
      }
    }
    else {
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
