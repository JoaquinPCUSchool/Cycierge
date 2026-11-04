// esp32 (not camera)

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#define RXD2 26
#define TXD2 27

String ipVar = "192.168.0.100";
String roomID = "2";

int voltage;
int status;

const char* WIFI_SSID = "samplemesh";
const char* WIFI_PASSWORD = "12345678";



void getData() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected!");
    return;
  }
  WiFiClient client;
  HTTPClient http;
  Serial.println("\nRequesting data from Raspberry Pi...");
  if (!http.begin(client, "http://" + ipVar + "/cycierge/user/getdata.php")) {
    Serial.println("HTTP begin failed!");
    return;
  }
  http.setTimeout(5000);
  int httpCode = http.GET();
  Serial.print("HTTP Response Code: ");
  Serial.println(httpCode);

  if (httpCode == HTTP_CODE_OK) {
    String response = http.getString();

    // Parse JSON array
    DynamicJsonDocument doc(2048);
    DeserializationError error = deserializeJson(doc, response);
    if (error) {
      Serial.print("JSON parsing failed: ");
      Serial.println(error.c_str());
      http.end();
      return;
    }
    if (!doc.is<JsonArray>()) {
      Serial.println("Error: JSON response is not an array.");
      http.end();
      return;
    }
    JsonArray users = doc.as<JsonArray>();
    if (users.size() == 0) {
      Serial.println("No data received.");
      http.end();
      return;
    }
    for (int x = 0; x < 2; x++) {
      JsonObject user = users[x];
      Serial.println("\n===== USER DATA =====");
      if (String(user["ID"] | "") == roomID) {

        Serial.print("ID: ");
        Serial.println(user["ID"] | "");
        Serial.print("Lock: ");
        Serial.println(user["USERLOCK"] | "");
        if (String(user["USERLOCK"] | "") == "1") {
          Serial2.println("1");
          delay(200);
          String dataLocksss = "0";
          postLockerData(dataLocksss);
        }
      }
      Serial.println("=====================");
    }
  } else {
    Serial.print("HTTP error: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();
}


void postMyd(String BattVarm, String CamVarm) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected!");
    return;
  }
  // Build JSON payload
  DynamicJsonDocument doc(512);
  doc["USERCAM"] = CamVarm;
  doc["USERBATT"] = BattVarm;
  doc["ID"] = roomID;
  String jsonPayload;
  serializeJson(doc, jsonPayload);

  Serial.println("\nSending POST request...");
  Serial.println("JSON payload:");
  Serial.println(jsonPayload);

  WiFiClient client;
  HTTPClient http;

  http.setConnectTimeout(5000);
  http.setTimeout(5000);

  if (!http.begin(client, "http://" + ipVar + "/cycierge/user/updatedata.php?")) {
    Serial.println("HTTP begin failed!");
    return;
  }
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Accept", "application/json");

  int httpCode = http.POST(jsonPayload);
  Serial.print("HTTP Response Code: ");
  Serial.println(httpCode);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.println("PHP response:");
    Serial.println(response);

    DynamicJsonDocument result(512);
    DeserializationError error = deserializeJson(result, response);

    if (!error) {
      bool success = result["success"] | false;
      if (success) {
        Serial.println("INSERT SUCCESS!");

        Serial.print("Inserted ID: ");
        Serial.println(
          result["inserted_id"] | "unknown");
      } else {
        Serial.print("Insert failed: ");
        Serial.println(
          result["message"] | "Unknown error");
      }
    } else {
      Serial.println("Response was not valid JSON.");
    }
  } else {
    Serial.print("POST error: ");
    Serial.println(http.errorToString(httpCode));
  }
  http.end();
}




void postLockerData(String LockVarm) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected!");
    return;
  }
  // Build JSON payload
  DynamicJsonDocument doc(512);

  doc["USERLOCK"] = LockVarm;
  doc["ID"] = roomID;
  String jsonPayload;
  serializeJson(doc, jsonPayload);

  Serial.println("\nSending POST request...");
  Serial.println("JSON payload:");
  Serial.println(jsonPayload);

  WiFiClient client;
  HTTPClient http;

  http.setConnectTimeout(5000);
  http.setTimeout(5000);

  if (!http.begin(client, "http://" + ipVar + "/cycierge/user/updatelock.php?")) {
    Serial.println("HTTP begin failed!");
    return;
  }
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Accept", "application/json");

  int httpCode = http.POST(jsonPayload);
  Serial.print("HTTP Response Code: ");
  Serial.println(httpCode);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.println("PHP response:");
    Serial.println(response);

    DynamicJsonDocument result(512);
    DeserializationError error = deserializeJson(result, response);

    if (!error) {
      bool success = result["success"] | false;
      if (success) {
        Serial.println("INSERT SUCCESS!");

        Serial.print("Inserted ID: ");
        Serial.println(
          result["inserted_id"] | "unknown");
      } else {
        Serial.print("Insert failed: ");
        Serial.println(
          result["message"] | "Unknown error");
      }
    } else {
      Serial.println("Response was not valid JSON.");
    }
  } else {
    Serial.print("POST error: ");
    Serial.println(http.errorToString(httpCode));
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  Serial2.setRxBufferSize(1024);

  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);

  Serial2.setTimeout(50);
}

unsigned long lastPost = 0;
String latestLine = "";

void loop() {
  getData();

  // Drain everything the Nano sent; keep only the newest complete line
  while (Serial2.available()) {
    String line = Serial2.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) latestLine = line;
  }

  if (latestLine.length() > 0 && millis() - lastPost >= 5000) {
    int comma = latestLine.indexOf(',');
    if (comma > 0) {
      voltage = constrain(latestLine.substring(0, comma).toInt(), 0, 100);
      status = latestLine.substring(comma + 1).toInt();
      Serial.printf("voltage: %d  status: %d\n", voltage, status);
      postMyd(String(voltage), String(status));
      lastPost = millis();
    }
    latestLine = "";
  }

  delay(200);
}
