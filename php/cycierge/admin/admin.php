<?php
   session_start();
   $_SESSION["userflag"] = "";
?>
<html>
<head>
	<title>Admin | CyCierge</title>
	<link rel="stylesheet" href="style.css">
</head>

<body>


	<?php
		if (isset($_POST['btn1'])) {
			$_SESSION["userflag"] = "1";
			header('Location: Edit.php');
			exit;
		}
		if (isset($_POST['btnview1'])) {
			$_SESSION["userflag"] = "1";
			header('Location: camera.php');
			exit;
		}

		if (isset($_POST['btnunlock1'])) {
			$host = "localhost";
			$username = "USER";
			$password = "12345678";
			$database = "MYDB";

			// Connect to MySQL
			$now = new DateTime(null, new DateTimeZone('Asia/Manila'));
			$datenow = $now->format('Y-m-d');
			$timenow = $now->format('H:i:s');
			$conn = new mysqli($host, $username, $password, $database);
			$stmt = $conn->prepare("UPDATE TBLUSER SET USERLOCK = '1' WHERE iD = 1");
			$stmt->execute();
			$stmt = $conn->prepare("INSERT INTO TBLLOGS (LOGSID, LOGSDATE, LOGSTIME, LOGSACTIVITY) VALUES (?, ?, ?, ?)");
			$stmt->execute(["2",$datenow,$timenow,"Admin Unlock Door"]);
			header('Location: admin.php');
			exit;
		}

		if (isset($_POST['btn2'])) {
			$_SESSION["userflag"] = "2";
			header('Location: Edit.php');
			exit;
		}
		if (isset($_POST['btnview2'])) {
			$_SESSION["userflag"] = "2";
			header('Location: camera.php');
			exit;
		}

		if (isset($_POST['btnunlock2'])) {
			$host = "localhost";
			$username = "USER";
			$password = "12345678";
			$database = "MYDB";

			// Connect to MySQL
			$now = new DateTime(null, new DateTimeZone('Asia/Manila'));
			$datenow = $now->format('Y-m-d');
			$timenow = $now->format('H:i:s');
			$conn = new mysqli($host, $username, $password, $database);
			$stmt = $conn->prepare("UPDATE TBLUSER SET USERLOCK = '1' WHERE iD = 2");
			$stmt->execute();
			$stmt = $conn->prepare("INSERT INTO TBLLOGS (LOGSID, LOGSDATE, LOGSTIME, LOGSACTIVITY) VALUES (?, ?, ?, ?)");
			$stmt->execute(["2",$datenow,$timenow,"Admin Unlock Door"]);
			header('Location: admin.php');
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
					

					if ($row["ID"] == "1") {
						echo "<H2> Room | 1 </H2>";
						
						echo "<label>NAME:  " . $row["USERNAME"] . "</label>";
						

						$tz = new DateTimeZone('Asia/Singapore');
						$date2 = new DateTime('now', $tz);
						$date1 = new DateTime($row["USERDATE"] . " " . $row["USERTIME"], $tz);
						$interval = $date1->diff($date2);
						echo "<label>TIME STAYED:  " . $interval->format('%d days, %h hours, %i minutes'). "</label>";

						echo "<label>BATTERY LEVEL:  " . $row["USERBATT"] . "% </label>";
					}
				}

			}
			$conn->close();

		?>
		<form method="POST" action="#">
			<div class="form-field">
				<button class="btn" type="submit" name="btn1">Edit</button>
				<button class="btn" type="submit" name="btnview1">View Cam</button>
				<button class="btn" type="submit" name="btnunlock1">Unlock Door</button>
			</div>
		</form>
	</div>

	</Br>


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
				

				if ($row["ID"] == "2") {
					echo "<H2> Room | 2 </H2>";
					echo "<label>NAME:  " . $row["USERNAME"] . "</label>";
					

					$tz = new DateTimeZone('Asia/Singapore');
					$date2 = new DateTime('now', $tz);
					$date1 = new DateTime($row["USERDATE"] . " " . $row["USERTIME"], $tz);
					$interval = $date1->diff($date2);
					echo "<label>TIME STAYED:  " . $interval->format('%d days, %h hours, %i minutes'). "</label>";

					echo "<label>BATTERY LEVEL:  " . $row["USERBATT"] . " %</label>";
				}
		    }

		} else {
		    echo "No data found.";
		}

		$conn->close();

	?>
	<form method="POST" action="#">
		<div class="form-field">
			<button class="btn" type="submit" name="btn2">Edit</button>
			<button class="btn" type="submit" name="btnview2">View Cam</button>
			<button class="btn" type="submit" name="btnunlock2">Unlock Door</button>
		</div>
	</form>
</div>
</body>
</html>