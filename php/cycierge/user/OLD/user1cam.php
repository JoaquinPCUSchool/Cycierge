<?php
	session_start();
	if (empty($_SESSION["userid"])) {
		echo '<script>alert("Please Login First");
			 window.location.href="userlogin.php";</script>';
	}
?>


<!DOCTYPE html>
<html>

<head>
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
	<link rel="stylesheet" href="style.css">

    <title>Room | 1 (Camera)</title>


</head>

<body>

<div class="main">




	<img id="myImage" src="http://192.168.5.171/stream" alt="Changeable Image">
    <button onclick="changeImageAndGo()">Back</button>

	<script>
        function changeImageAndGo() {
            // 1. Change the image source
            var img = document.getElementById("myImage");
            img.src = "new_image.jpg";
            img.onload = function() {
                window.location.href = "user1.php"; 
            };
            setTimeout(function() {
                window.location.href = "user1.php";
            }, 5); // Redirects after 1 second if onload doesn't trigger
        }
    </script>


</div>
</body>
</html>