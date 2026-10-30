<?php
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

				if ($uname == $row["USERID"] and $upass == $row["USERPASS"]) {
					$_SESSION["userid"] = $uname;

					if ($row["ID"] == "1") {
						$_SESSION["usernum"] = "1";
					}
					if ($row["ID"] == "2") {
						$_SESSION["usernum"] = "2";	
					}
					header('Location: user.php');
					exit;
					
				} 
				else {
					echo '<script type="text/javascript"> myFunction(); </script>';
				}
		    }

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