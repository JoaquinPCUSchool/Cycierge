<?php
	session_start();
	if (empty($_SESSION["userid"])) {
		echo '<script>alert("Please Login First");
			 window.location.href="Login.php";</script>';
	}
?>


<!DOCTYPE html>
<html>

<head>
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
	<link rel="stylesheet" href="style.css">

	<?php
		if ($_SESSION["usernum"] == "1") {
			echo "<title>Room | 1 (Camera)</title>";
		}
		else {
			echo "<title>Room | 2 (Camera)</title>";
		}
	?>
</head>

<body>

<div class="main">

	<script>
        function changeImageAndGo() {
            // 1. Change the image source
            var img = document.getElementById("myImage");
            img.src = "new_image.jpg";
            img.onload = function() {
                window.location.href = "user.php"; 
            };
            setTimeout(function() {
                window.location.href = "user.php";
            }, 5); // Redirects after 1 second if onload doesn't trigger
        }
    </script>



	<?php
		if ($_SESSION["usernum"] == "1") { 
	?>	
		<img id="myImage" src="http://192.168.0.111/stream" alt="Changeable Image">
	<?php 
		}
		else {
	?>	
		<img id="myImage" src="http://192.168.0.121/stream" alt="Changeable Image">
	<?php 
		}
	?>

    <button onclick="changeImageAndGo()">Back</button>

</div>
</body>
</html>