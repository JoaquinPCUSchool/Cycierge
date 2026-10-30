<?php
	session_start();
	if (empty($_SESSION["userid"])) {
		echo '<script>alert("Please Login First");
			 window.location.href="Login.php";</script>';
	}
?>

<?php
	// Refreshes the current page every 5 seconds
	header("Refresh: 25");
?>

<!DOCTYPE html>
<html>

<head>
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
	<link rel="stylesheet" href="style.css">

	
	<?php
		if ($_SESSION["usernum"] == "1") {
			echo "<title>Room | 1</title>";
		}
		else {
			echo "<title>Room | 2</title>";
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

			$now = new DateTime(null, new DateTimeZone('Asia/Manila'));
			$datenow = $now->format('Y-m-d');
			$timenow = $now->format('H:i:s');
			if ($_SESSION["usernum"] == "1") {
				
				$stmt = $conn->prepare("UPDATE TBLUSER SET USERLOCK = '1' WHERE iD = 1");
				$stmt->execute();
				$stmt = $conn->prepare("INSERT INTO TBLLOGS (LOGSID, LOGSDATE, LOGSTIME, LOGSACTIVITY) VALUES (?, ?, ?, ?)");
				$stmt->execute(["1",$datenow,$timenow,"User1 Unlock Door"]);
			}
			else {
				$stmt = $conn->prepare("UPDATE TBLUSER SET USERLOCK = '1' WHERE iD = 2");
				$stmt->execute();
				$stmt = $conn->prepare("INSERT INTO TBLLOGS (LOGSID, LOGSDATE, LOGSTIME, LOGSACTIVITY) VALUES (?, ?, ?, ?)");
				$stmt->execute(["2",$datenow,$timenow,"User2 Unlock Door"]);
				
			}
			//header('Location: user.php');
			//exit;
		}


		if (isset($_POST['btnView'])) {
			header('Location: camera.php');
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

				//echo "ID: " . $row["ID"] . "<br>";
				//echo "Name: " . $row["USERID"] . "<br>";
				//echo "Email: " . $row["USERPASS"] . "<br>";

				//echo "<hr>";

				if ($row["ID"] == $_SESSION["usernum"]) {

					echo "<label> NAME: </label>";
					echo "<h2>" . $row["USERNAME"] . "</h2>";

					echo "<label> BATTERY PERCENTAGE: </label>";
					echo "<h2> " . $row["USERBATT"] . " %</h2>";

					$tz = new DateTimeZone('Asia/Singapore');

					// Create the two dates (example: now and a past date)
					$date2 = new DateTime('now', $tz);
					$date1 = new DateTime($row["USERDATE"] . " " . $row["USERTIME"], $tz);

					// Calculate the difference
					$interval = $date1->diff($date2);

					//echo "$days days, $hours hours, $minutes minutes";
					echo "<label> TIME STAYED: </label>";
					echo "<h2>" . $interval->format('%d days, %h hours, %i minutes'). "</h2>";
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

				if ($row["LOGSID"] == "1") {
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
		echo "</table>";
	?>


</div>
</body>
</html>