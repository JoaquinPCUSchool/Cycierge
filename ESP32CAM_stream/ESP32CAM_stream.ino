// ESP32-CAM (AI-Thinker) live MJPEG stream + snapshot
// v2: hardware JPEG (OV2640) with automatic RGB565 + software-JPEG fallback
//     (for sensors like the GC2145 / M21-45), heartbeat logging, safer WiFi.
//
// Arduino IDE: Board = "AI Thinker ESP32-CAM", Partition = "Huge APP"
// To flash: hold/short GPIO0 to GND, press RESET, upload,
// then remove GPIO0 from GND and press RESET again.

#include "esp_camera.h"
#include "esp_system.h"
#include <WiFi.h>
#include <WebServer.h>

//        TENANT  RPI   ADMIN
//ROOM 1: 111     112   113
//ROOM 2: 121     122   123

// ---- PER-CAM SETTINGS: change the last octet for each board you flash ----
IPAddress local_IP(192, 168, 0, 111);
IPAddress gateway(192, 168, 0, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);

const char *ssid = "samplemesh";
const char *password = "12345678";

// ---- TUNING KNOBS (change one at a time) ----
#define FRAME_SIZE FRAMESIZE_QVGA   // QVGA 320x240 -> try VGA 640x480 once stable
#define HW_JPEG_QUALITY 12          // hardware JPEG: 10 (best) .. 63 (worst)
#define SW_JPEG_QUALITY 60          // fallback software JPEG: 0..100 (higher = better)
#define FRAME_DELAY_MS 66           // ~15 fps cap in /stream
#define TX_POWER WIFI_POWER_15dBm   // try 19_5dBm / 15dBm / 11dBm; lower = smaller current peaks

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

WebServer server(80);

// =====================================================
// Camera setup
// =====================================================

static bool initCamera(pixformat_t fmt) {
  camera_config_t config = {};

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
  config.pixel_format = fmt;
  config.frame_size = FRAME_SIZE;
  config.jpeg_quality = HW_JPEG_QUALITY;  // only used when fmt == PIXFORMAT_JPEG

  if (psramFound()) {
    config.fb_count = 2;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    config.fb_count = 1;
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("esp_camera_init(%s) failed: 0x%x\n",
                  fmt == PIXFORMAT_JPEG ? "JPEG" : "RGB565", err);
    return false;
  }
  return true;
}

bool setupCamera() {
  // 1) Hardware JPEG (OV2640): no CPU encoding, small frames, less heat/current/airtime.
  if (initCamera(PIXFORMAT_JPEG)) {
    Serial.println("Camera mode: HARDWARE JPEG");
  } else {
    // 2) Fallback for sensors without JPEG (e.g. GC2145 / M21-45): RGB565 + software encode.
    esp_camera_deinit();
    if (!initCamera(PIXFORMAT_RGB565)) return false;
    Serial.println("Camera mode: RGB565 + SOFTWARE JPEG (slower, heavier)");
  }

  sensor_t *sensor = esp_camera_sensor_get();
  if (sensor) {
    Serial.printf("Sensor PID: 0x%04X (OV2640 = 0x26)\n", sensor->id.PID);
  }
  return true;
}

// =====================================================
// JPEG grab helpers (work for both camera modes)
// =====================================================

// NOTE: plain types only in these signatures. The Arduino IDE auto-generates
// prototypes above any struct defined in the sketch, which breaks compilation.

// Grab one JPEG. Returns true on success.
// Hardware-JPEG mode: *fb is set and *buf points into it.
// Software mode:      *fb is nullptr and *buf is a malloc'd buffer.
// Always call releaseJpeg() afterwards.
bool grabJpeg(camera_fb_t **fb, uint8_t **buf, size_t *len) {
  *fb = nullptr;
  *buf = nullptr;
  *len = 0;

  camera_fb_t *f = esp_camera_fb_get();
  if (!f) return false;

  if (f->format == PIXFORMAT_JPEG) {
    *fb = f;
    *buf = f->buf;
    *len = f->len;
    return true;
  }

  bool ok = frame2jpg(f, SW_JPEG_QUALITY, buf, len);
  esp_camera_fb_return(f);
  return ok;
}

void releaseJpeg(camera_fb_t **fb, uint8_t **buf) {
  if (*fb) esp_camera_fb_return(*fb);
  else if (*buf) free(*buf);
  *fb = nullptr;
  *buf = nullptr;
}

// =====================================================
// Housekeeping: heartbeat + WiFi watchdog
// Called from loop() AND from the stream loop (which blocks loop()).
// =====================================================

void housekeeping() {
  static uint32_t lastBeat = 0;
  static uint32_t downSince = 0;
  uint32_t now = millis();

  if (WiFi.status() != WL_CONNECTED) {
    if (!downSince) downSince = now;
    if (now - downSince > 30000) {
      Serial.println("WiFi down >30s, restarting");
      ESP.restart();
    }
  } else {
    downSince = 0;
  }

  if (now - lastBeat >= 5000) {
    lastBeat = now;
    Serial.printf("[hb] up=%lus wifi=%d rssi=%d heap=%u minheap=%u\n",
                  (unsigned long)(now / 1000), (int)WiFi.status(), WiFi.RSSI(),
                  (unsigned)ESP.getFreeHeap(), (unsigned)ESP.getMinFreeHeap());
  }
}

// =====================================================
// Send one JPEG image
// =====================================================

void handleJPG() {
  camera_fb_t *fb;
  uint8_t *buf;
  size_t len;
  if (!grabJpeg(&fb, &buf, &len)) {
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }

  WiFiClient client = server.client();
  client.printf(
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: image/jpeg\r\n"
    "Content-Length: %u\r\n"
    "Connection: close\r\n\r\n",
    (unsigned int)len);
  client.write(buf, len);
  releaseJpeg(&fb, &buf);
}

// =====================================================
// MJPEG stream (blocks the server while a client is connected:
// keep to ONE stream client per cam; use /jpg for everything else)
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
    camera_fb_t *fb;
    uint8_t *buf;
    size_t len;
    if (!grabJpeg(&fb, &buf, &len)) {
      Serial.println("Frame grab/encode failed");
      break;
    }

    client.printf(
      "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",
      (unsigned int)len);
    size_t written = client.write(buf, len);
    client.print("\r\n");
    releaseJpeg(&fb, &buf);

    if (written != len) {
      Serial.printf("Short write (%u/%u), dropping client\n",
                    (unsigned)written, (unsigned)len);
      break;
    }

    housekeeping();
    delay(FRAME_DELAY_MS);
  }
  client.stop();
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
  Serial.println("ESP32-CAM LIVE STREAM v2");
  Serial.println("==============================");

  // Evidence for power problems. Do NOT disable the brownout detector;
  // it is the best clue you have.
  Serial.printf("Reset reason: %d (brownout = %d)\n",
                (int)esp_reset_reason(), (int)ESP_RST_BROWNOUT);

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
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);

  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS)) {
    Serial.println("Static IP configuration failed");
  }

  WiFi.begin(ssid, password);

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

  WiFi.setSleep(false);       // no modem sleep (latency spikes)
  WiFi.setTxPower(TX_POWER);  // lower peaks if the 5V rail is marginal

  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("ESP32-CAM IP: ");
  Serial.println(WiFi.localIP());
  Serial.printf("RSSI: %d dBm, channel: %d, BSSID: %s\n",
                WiFi.RSSI(), WiFi.channel(), WiFi.BSSIDstr().c_str());

  server.on("/", HTTP_GET, handleRoot);
  server.on("/jpg", HTTP_GET, handleJPG);
  server.on("/stream", HTTP_GET, handleStream);
  server.begin();

  Serial.println("HTTP server started");
}

// =====================================================
// Loop
// =====================================================

void loop() {
  server.handleClient();
  housekeeping();
}
