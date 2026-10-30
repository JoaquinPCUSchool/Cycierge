<?php
	session_start();
	if (empty($_SESSION["userid"])) {
		echo '<script>alert("Please Login First");
			 window.location.href="userlogin.php";</script>';
	}
?>

<?php
	// Refreshes the current page every 5 seconds
	header("Refresh: 5");
?>

<!DOCTYPE html>
<html>

<head>
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
	<link rel="stylesheet" href="style.css">

	

    <title>Room | 2</title>

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

	<?php
		

		if (isset($_POST['btnunlock'])) {

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
			$stmt = $conn->prepare("UPDATE TBLUSER SET USERLOCK = '1' WHERE id = 1");
			$stmt->execute();


			header('Location: user2.php');
			exit;

		}


		if (isset($_POST['btnView'])) {
			echo "Hello world!";
			header('Location: user2cam.php');
			exit;
		}


	?>



<div class="main">

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
		$sql = "SELECT * FROM TBLUSER";
		$result = $conn->query($sql);

		// Print each row
		if ($result->num_rows > 0) {

		    while ($row = $result->fetch_assoc()) {

				if ($row["ID"] == "2") {
					?>
					<label for="first"> Name: </label>
					<?php
					echo "<h1>" . $row["USERNAME"] . "</h1>";

					?>
					<label for="first"> Battery Percentage: </label>
					<?php
					echo "<h1> " . $row["USERBATT"] . "</h1>";

					$tz = new DateTimeZone('Asia/Singapore');

					// Create the two dates (example: now and a past date)
					$date2 = new DateTime('now', $tz);
					$date1 = new DateTime($row["USERDATE"] . " " . $row["USERTIME"], $tz);

					// Calculate the difference
					$interval = $date1->diff($date2);

					//echo "$days days, $hours hours, $minutes minutes";
					?>	
					<label for="first"> Time Stayed: </label>
					<?php
					#echo "<h1>" . "$days days, $hours hours, $minutes minutes" . "</h1>";
					echo "<h1>" . $interval->format('%d days, %h hours, %i minutes'). "</h1>";
				}
		    }

		} else {
		    echo "No data found.";
		}

		$conn->close();

	?>


	<form method="POST" action="#">
		<div class="form-field">
			<button class="btn" type="submit" name="btnunlock">Unlock Door</button>
		</div>

		<div class="form-field">
			<button class="btn" type="submit" name="btnView">View Cam</button>
		</div>
	</form>


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

				if ($row["LOGSID"] == "2") {
					echo "<tr>";
					echo "<td>". $row["LOGSDATE"] ."</td>";
					echo "<td>". $row["LOGSTIME"] ."</td>";
					echo "<td>". $row["LOGSACTIVITY"] ."</td>";
					echo "</tr>";
					
				}
		    }

		} else {
		    echo "No data found.";
		}

		$conn->close();
	?>
</div>
</body>
</html>