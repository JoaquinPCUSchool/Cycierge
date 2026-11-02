<?php require_once __DIR__ . '/../throttle.php'; require_once '/etc/cycierge/config.php';
   session_start();
   $_SESSION["userid"] = "";
   $_SESSION["usernum"] = "";
?>

<html>
<head>
	<title>Login | CyCierge</title>
	<link rel="stylesheet" href="style.css">
	<script>
		function myFunction() {
			alert("UserID or Password is INCORRECT !");
		}
	</script>
</head>

<body>
	<?php

	if (isset($_POST['usernamevar'])) {

		$uname = $_POST['usernamevar'];
		$upass = $_POST['userpassvar'];
        $blocked = login_blocked($uname);


		$host = "localhost";
		$username = DB_USER;
		$password = DB_PASS;
		$database = DB_NAME;

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
		if ($blocked) {
            echo '<script type="text/javascript"> alert("Too many failed attempts. Try again in 10 minutes."); </script>';
        } elseif ($result->num_rows > 0) {

		    while ($row = $result->fetch_assoc()) {
				//echo "ID: " . $row["ID"] . "<br>";

				if (hash_equals((string)$row["USERID"], (string)$uname) && password_verify((string)$upass, (string)$row["USERPASS"])) {
					session_regenerate_id(true);
					$_SESSION["userid"] = $uname;

					if ($row["ID"] == "1") {
						$_SESSION["usernum"] = "1";
					}
					if ($row["ID"] == "2") {
						$_SESSION["usernum"] = "2";	
					}
					login_ok($uname);
                    header('Location: user.php');
					exit;
					
				} 
				else {
					echo '<script type="text/javascript"> myFunction(); </script>';
				}
		    }
            login_failed($uname);

        } else {
            echo "No data found.";
		}

		$conn->close();
		
	}
	?>



	<div class="main">

		<h1>CyCierge</h1>
        <h3>Enter your login credentials</h3>


		<form method="POST" action="#">
			<div class="form-field">
				<label for="first"> Username: </label>
				<input type="text" name="usernamevar" placeholder="User Name" required />
			</div>

			<div class="form-field">
				<label for="password"> Password: </label>
				<input type="password" name="userpassvar" placeholder="Password" required />
			</div>
			<div class="form-field">
				<button class="btn" type="submit" value="btnlogin">Log in</button>

			</div>
		</form>
	</div>
</body>
</html>