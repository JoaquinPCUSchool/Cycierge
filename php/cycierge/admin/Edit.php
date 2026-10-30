<?php
	session_start();
	if (empty($_SESSION["userflag"])) {
		echo '<script>alert("Ask Admin to Login..");
			 window.location.href="userlogin.php";</script>';
	}
?>
<html>
<head>
	<title>Admin | CyCierge</title>
	<link rel="stylesheet" href="style.css">
</head>
<body>

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

				if ($row["ID"] == $_SESSION["userflag"]) {
					$name = $row["USERNAME"];
					$id = $row["USERID"];
					$pass = $row["USERPASS"];
				}
		    }

		} else {
		    echo "No data found.";
		}
		$conn->close();
	?>




	<?php
		if (isset($_POST['btnupdate'])) {

			$unamevar = $_POST['namevar'];
			$uidvar = $_POST['idvar'];
			$upassvar = $_POST['passvar'];

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
			$stmt = $conn->prepare("UPDATE TBLUSER SET USERNAME = '" . $unamevar . "', USERID = '". $uidvar ."', USERPASS = '". $upassvar ."' WHERE ID = '".$_SESSION["userflag"]."'");
			$stmt->execute();


			header('Location: admin.php');
			exit;

		}
	?>

	<div class="main">
		<form method="post" action="Edit.php">
			<label>Name:
				<input type="text" name="namevar" 
				       value="<?php echo $name ?>">
			</label>

			<label>Id:
				<input type="text" name="idvar" 
				       value="<?php echo $id ?>">
			</label>

			<label>Password:
				<input type="text" name="passvar" 
				       value="<?php echo $pass ?>">
			</label>
			
			<form method="POST" action="#">
				<div class="form-field">
					<button class="btn" type="submit" name="btnupdate">UPDATE</button>
				</div>
			</form>
		</form>

		</div>
	</div>
</body>
</html>