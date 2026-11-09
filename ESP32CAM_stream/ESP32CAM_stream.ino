// ESP32-CAM (AI-Thinker, OV2640) live MJPEG stream
// Works with or without PSRAM.
//
// Arduino IDE: Board = "AI Thinker ESP32-CAM", Partition = "Huge APP"
// To flash: hold/short GPIO0 to GND, press RESET, upload,
// then remove GPIO0 from GND and press RESET again.

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

//        TENANT  RPI   ADMIN
//ROOM 1: 111     112   113
//ROOM 2: 121     122   123

IPAddress local_IP(192, 168, 0, 122);
IPAddress gateway(192, 168, 0, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);

// =====================================================
// WiFi
// =====================================================

const char *ssid = "samplemesh";
const char *password = "12345678";

// =====================================================
// AI-Thinker ESP32-CAM pins
// =====================================================

#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5

#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

// =====================================================

WebServer server(80);

// =====================================================
// Camera setup
// =====================================================

bool setupCamera() {
  camera_config_t config = {};  // zero everything first

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;

  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_RGB565;  // correct for OV2640

  if (psramFound()) {
    Serial.println("PSRAM found: using PSRAM frame buffers");
    config.frame_size = FRAMESIZE_QVGA;  // 640x480
    config.jpeg_quality = 18;
    config.fb_count = 2;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    Serial.println("No PSRAM: using DRAM frame buffers (QVGA)");
    config.frame_size = FRAMESIZE_QVGA;  // 320x240
    config.jpeg_quality = 15;
    config.fb_count = 1;
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  }

  esp_err_t err = esp_camera_init(&config);

  if (err != ESP_OK) {
    Serial.printf("Camera initialization failed: 0x%x\n", err);
    return false;
  }

  Serial.println("Camera initialized!");

  sensor_t *sensor = esp_camera_sensor_get();
  if (sensor) {
    Serial.printf("Sensor PID: 0x%04X (OV2640 = 0x26)\n", sensor->id.PID);
  }

  return true;
}

// =====================================================
// Send one JPEG image
// =====================================================

void handleJPG() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }

  uint8_t *jpg_buf = nullptr;
  size_t jpg_len = 0;
  bool ok = frame2jpg(fb, 80, &jpg_buf, &jpg_len);  // quality 0-100, higher = better
  esp_camera_fb_return(fb);

  if (!ok) {
    server.send(500, "text/plain", "JPEG conversion failed");
    return;
  }

  WiFiClient client = server.client();
  client.printf(
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: image/jpeg\r\n"
    "Content-Length: %u\r\n"
    "Connection: close\r\n\r\n",
    (unsigned int)jpg_len);
  client.write(jpg_buf, jpg_len);
  free(jpg_buf);
}

// =====================================================
// MJPEG stream
// =====================================================

void handleStream() {
  WiFiClient client = server.client();

  client.print(
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
    "Cache-Control: no-cache\r\n"
    "Pragma: no-cache\r\n"
    "Connection: close\r\n\r\n");

  while (client.connected()) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      break;
    }

    uint8_t *jpg_buf = nullptr;
    size_t jpg_len = 0;
    bool ok = frame2jpg(fb, 80, &jpg_buf, &jpg_len);
    esp_camera_fb_return(fb);
    if (!ok) {
      Serial.println("JPEG conversion failed");
      break;
    }

    client.printf(
      "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",
      (unsigned int)jpg_len);
    client.write(jpg_buf, jpg_len);
    client.print("\r\n");
    free(jpg_buf);

    delay(50);
  }
}

// =====================================================
// Web page
// =====================================================

void handleRoot() {
  String page = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ESP32 Camera</title>
<style>
body { background: #111; color: white; font-family: Arial; text-align: center; }
img { width: 100%; max-width: 640px; }
</style>
</head>
<body>
<h1>ESP32-CAM</h1>
<img src="/stream">
<p>Live video</p>
</body>
</html>
)rawliteral";

  server.send(200, "text/html", page);
}

// =====================================================
// Setup
// =====================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("==============================");
  Serial.println("ESP32-CAM LIVE STREAM");
  Serial.println("==============================");

  Serial.printf("PSRAM found: %s, size: %u\n",
                psramFound() ? "yes" : "no",
                (unsigned int)ESP.getPsramSize());

  Serial.println("Initializing camera...");
  if (!setupCamera()) {
    Serial.println("Camera failed. Restarting in 5 seconds...");
    delay(5000);
    ESP.restart();
  }

  Serial.println("Configuring WiFi...");
  WiFi.mode(WIFI_STA);

  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS)) {
    Serial.println("Static IP configuration failed");
  }

  WiFi.begin(ssid, password);

  WiFi.setSleep(false);

  Serial.print("Connecting to WiFi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - start > 20000) {
      Serial.println();
      Serial.println("WiFi timeout. Restarting...");
      ESP.restart();
    }
  }

  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("ESP32-CAM IP: ");
  Serial.println(WiFi.localIP());

  server.on("/", HTTP_GET, handleRoot);
  server.on("/jpg", HTTP_GET, handleJPG);
  server.on("/stream", HTTP_GET, handleStream);
  server.begin();

  Serial.println("HTTP server started");
  Serial.println("Open the IP address in a browser.");
}

// =====================================================
// Loop
// =====================================================

void loop() {
  server.handleClient();

  // Reconnect if WiFi drops
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi lost, reconnecting...");
    WiFi.disconnect();
    WiFi.begin(ssid, password);
    delay(3000);
  }
}
