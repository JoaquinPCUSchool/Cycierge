<?php
	session_start();
	if (empty($_SESSION["adminid"])) {
		echo '<script>alert("Please Login First");
			 window.location.href="adminlogin.php";</script>';
	}
?>


<!DOCTYPE html>
<html>

<head>
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
	<link rel="stylesheet" href="style.css">

	<?php
	if ($_SESSION["userflag"] == "1") {
		echo "<title>Room | 1 (Admin View)</title>";
	}
	else {
		echo "<title>Room | 2 (Admin View)</title>";
	}
	?>
    

<style>
		table {
		  font-family: arial, sans-serif;
		  border-collapse: collapse;
		  width: 100%;
		}

		td{
		  border: 1px solid #3B93AD;
		  text-align: left;
		  padding: 8px;
		}

		th {
		  border: 1px solid #3B93AD;
		  text-align: left;
		  padding: 8px;
		  background-color: #3B93AD;
		}	


		tr:nth-child(even) {
		  background-color: #dddddd;
		}
	</style>


</head>

<body>

<script>
        function changeImageAndGo() {
            // 1. Change the image source
            var img = document.getElementById("myImage");
            img.src = "new_image.jpg";
            img.onload = function() {
                window.location.href = "admin.php"; 
            };
            setTimeout(function() {
                window.location.href = "admin.php";
            }, 5); // Redirects after 1 second if onload doesn't trigger
        }
    </script>




<div class="main">

	<?php
		if ($_SESSION["userflag"] == "1" ) {
	?>
			<img id="myImage" src="http://192.168.5.72/stream" alt="Changeable Image">
	<?php	
		}
		else {
		?>	
			<img id="myImage" src="http://192.168.5.62/stream" alt="Changeable Image">
	<?php

		}
	?>

	
    <button onclick="changeImageAndGo()">Back</button>

	


	<?php
		$host = "localhost";
		$username = "USER";
		$password = "12345678";
		$database = "MYDB";

		// Connect to MySQL
		$conn = new mysqli($host, $username, $password, $database);

		// Check connection
		if ($conn->connect_error) {
		    die("Connection failed: " . $conn->connect_error);
		}

		// Get data
		$sql = "SELECT * FROM TBLLOGS";
		$result = $conn->query($sql);

		// Print each row
		if ($result->num_rows > 0) {

			echo "<h2>ACTIVITY LOGS</h2>";
			echo "<table>";
			echo "<tr> <th>DATE</th> <th>TIME</th> <th>ACTIVITY</th> </tr>";

		    while ($row = $result->fetch_assoc()) {

				if ($row["LOGSID"] == $_SESSION["userflag"]) {
					echo "<tr>";
					echo "<td>". $row["LOGSDATE"] ."</td>";
					echo "<td>". $row["LOGSTIME"] ."</td>";
					echo "<td>". $row["LOGSACTIVITY"] ."</td>";
					echo "</tr>";
				}
		    }

		} else {
		    echo "<h3>No Activity Logs found.</h3>";
		}

		$conn->close();
		echo "</table>";
	?>

	<button onclick="myFunction()">DELETE ACTIVITY LOGS</button>


	<script>
		function myFunction() {
		  var txt;
		  if (confirm("Are you sure you want to DELETE all Activity Logs?")) {
					const form = document.createElement("form");
					form.method = "POST";
					form.action = "camera.php";

					const input = document.createElement("input");
					input.type = "hidden";
					input.name = "delete_all";
					input.value = "1";

					form.appendChild(input);
					document.body.appendChild(form);
					form.submit();
		  } else {
			txt = "You pressed Cancel!";
		  }
		  document.getElementById("demo").innerHTML = txt;
		}


		<?php
			if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST["delete_all"])) {
				$conn = new mysqli($host, $username, $password, $database);
				$conn = mysqli_connect("localhost", "USER", "12345678", "MYDB");
				$id = $_SESSION["userflag"]; // Get ID from URL or form
				$sql = "DELETE FROM TBLLOGS WHERE LOGSID = $id";
				mysqli_query($conn, $sql);

				$conn->close();
			}
		?>
	</script>
</form>
</div>
</body>
</html>