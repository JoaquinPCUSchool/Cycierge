#include "esp_camera.h"
#include "img_converters.h"
#include <WiFi.h>
#include <WebServer.h>

IPAddress local_IP(192, 168, 5, 72);
IPAddress gateway(192, 168, 5, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);

// =====================================================
// WiFi
// =====================================================

const char* ssid = "samplemesh";
const char* password = "12345678";

// =====================================================
// AI-Thinker ESP32-CAM pins
// =====================================================

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// =====================================================

WebServer server(80);

// =====================================================
// Camera setup
// =====================================================

void setupCamera()
{
  camera_config_t config;

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;

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

  // IMPORTANT
  // Your sensor works with RGB565
  config.pixel_format = PIXFORMAT_RGB565;

  // Start with QVGA for stability
  config.frame_size = FRAMESIZE_QVGA;

  config.jpeg_quality = 12;

  if (psramFound()) {
    config.fb_count = 2;
  } else {
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);

  if (err != ESP_OK) {
    Serial.printf(
      "Camera initialization failed: 0x%x\n",
      err
    );

    while (true) {
      delay(1000);
    }
  }

  Serial.println("Camera initialized!");

  sensor_t *sensor = esp_camera_sensor_get();

  if (sensor) {
    Serial.printf(
      "Sensor PID: 0x%04X\n",
      sensor->id.PID
    );
  }
}

// =====================================================
// Send one JPEG image
// =====================================================

void handleJPG()
{
  camera_fb_t *fb = esp_camera_fb_get();

  if (!fb) {
    server.send(
      500,
      "text/plain",
      "Camera capture failed"
    );

    return;
  }

  // Allocate JPEG buffer
  size_t jpgSize = 0;

  uint8_t *jpgBuffer = NULL;

  bool converted = fmt2jpg(
                     fb->buf,
                     fb->len,
                     fb->width,
                     fb->height,
                     PIXFORMAT_RGB565,
                     80,
                     &jpgBuffer,
                     &jpgSize
                   );

  esp_camera_fb_return(fb);

  if (!converted) {
    server.send(
      500,
      "text/plain",
      "JPEG conversion failed"
    );

    return;
  }

  server.sendHeader(
    "Content-Length",
    String(jpgSize)
  );

  server.send(
    200,
    "image/jpeg",
    ""
  );

  WiFiClient client = server.client();

  client.write(
    jpgBuffer,
    jpgSize
  );

  free(jpgBuffer);
}

// =====================================================
// MJPEG stream
// =====================================================

void handleStream()
{
  WiFiClient client = server.client();

  client.print(
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
    "Cache-Control: no-cache\r\n"
    "Pragma: no-cache\r\n"
    "Connection: close\r\n\r\n"
  );

  while (client.connected()) {

    camera_fb_t *fb =
      esp_camera_fb_get();

    if (!fb) {
      Serial.println(
        "Camera capture failed"
      );

      break;
    }

    uint8_t *jpgBuffer = NULL;
    size_t jpgSize = 0;

    bool converted = fmt2jpg(
                       fb->buf,
                       fb->len,
                       fb->width,
                       fb->height,
                       PIXFORMAT_RGB565,
                       70,
                       &jpgBuffer,
                       &jpgSize
                     );

    esp_camera_fb_return(fb);

    if (!converted) {
      Serial.println(
        "JPEG conversion failed"
      );

      break;
    }

    client.printf(
      "--frame\r\n"
      "Content-Type: image/jpeg\r\n"
      "Content-Length: %u\r\n"
      "\r\n",
      (unsigned int)jpgSize
    );

    client.write(
      jpgBuffer,
      jpgSize
    );

    client.print("\r\n");

    free(jpgBuffer);

    // Small delay to reduce CPU/network load
    delay(50);
  }
}

// =====================================================
// ESP32 web page
// =====================================================

void handleRoot()
{
  String page = R"rawliteral(
<!DOCTYPE html>

<html>

<head>
<meta name="viewport"
      content="width=device-width,initial-scale=1">

<title>ESP32 Camera</title>

<style>

body {
    background: #111;
    color: white;
    font-family: Arial;
    text-align: center;
}

img {
    width: 100%;
    max-width: 640px;
}

</style>

</head>

<body>

<h1>ESP32-CAM</h1>

<img src="/stream">

<p>Live video</p>

</body>

</html>
)rawliteral";

    server.send(
        200,
        "text/html",
        page
    );
}

// =====================================================
// Setup
// =====================================================

void setup()
{
    Serial.begin(115200);

    delay(1000);

    Serial.println();
    Serial.println("==============================");
    Serial.println("ESP32-CAM LIVE STREAM");
    Serial.println("==============================");

    if (!WiFi.config(local_IP, gateway, subnet, primaryDNS)) {
    Serial.println("Configuration failed");
    return;
  }

    setupCamera();

    // =================================================
    // WiFi
    // =================================================

    WiFi.begin(
        ssid,
        password
    );

    Serial.print(
        "Connecting to WiFi"
    );

    while (
        WiFi.status() != WL_CONNECTED
    ) {
        delay(500);

        Serial.print(".");
    }

    Serial.println();
    Serial.println(
        "WiFi connected!"
    );

    Serial.print(
        "ESP32-CAM IP: "
    );

    Serial.println(
        WiFi.localIP()
    );

    // =================================================
    // HTTP routes
    // =================================================

    server.on(
        "/",
        HTTP_GET,
        handleRoot
    );

    server.on(
        "/jpg",
        HTTP_GET,
        handleJPG
    );

    server.on(
        "/stream",
        HTTP_GET,
        handleStream
    );

    server.begin();

    Serial.println(
        "HTTP server started"
    );

    Serial.println(
        "Open the IP address in a browser."
    );
}

// =====================================================
// Loop
// =====================================================

void loop()
{
    server.handleClient();
}
