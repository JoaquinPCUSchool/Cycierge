<!DOCTYPE html>
<html>

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>ESP32-CAM Live</title>

    <style>

        body {
            margin: 0;
            background: #111;
            color: white;
            font-family: Arial, sans-serif;
            text-align: center;
        }

        h1 {
            margin: 25px;
        }

        .camera {
            width: 90%;
            max-width: 640px;
            margin: auto;
        }

        .camera img {
            width: 100%;
            display: block;
            border: 2px solid white;
        }

        .status {
            margin-top: 15px;
            color: lime;
        }

    </style>

</head>

<body>

<h1>ESP32-CAM Live Video</h1>

<div class="camera">

    <img
        src="http://192.168.5.171/stream"
        alt="Camera Stream"
    >

</div>

<div class="status">
    ? LIVE
</div>

</body>

</html>