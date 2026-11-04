<?php require_once '/etc/cycierge/config.php';
    require __DIR__ . '/auth.php';
    if (empty($_SESSION["userflag"])) { header('Location: admin.php'); exit; }
?>
<html>
<head>
	<title>Admin | CyCierge</title>
	<link rel="stylesheet" href="style.css">
</head>
<body>

	<?php
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
			$username = DB_USER;
			$password = DB_PASS;
			$database = DB_NAME;

			// Connect to MySQL
			$conn = new mysqli($host, $username, $password, $database);

			// Check connection
			if ($conn->connect_error) {
				die("Connection failed: " . $conn->connect_error);
			}
			$stmt = $conn->prepare("UPDATE TBLUSER SET USERNAME = ?, USERID = ?, USERPASS = COALESCE(?, USERPASS) WHERE ID = ?");
			$newhash = ($upassvar === '') ? null : password_hash($upassvar, PASSWORD_DEFAULT);
			$flag = (int)$_SESSION["userflag"];
			$stmt->bind_param("sssi", $unamevar, $uidvar, $newhash, $flag);
			$stmt->execute();


			header('Location: admin.php');
			exit;

		}
	?>

	<div class="main">
		<form method="post" action="Edit.php">
			<label>Name:
				<input type="text" name="namevar" 
				       value="<?php echo htmlspecialchars($name ?? '', ENT_QUOTES); ?>">
			</label>

			<label>Id:
				<input type="text" name="idvar" 
				       value="<?php echo htmlspecialchars($id ?? '', ENT_QUOTES); ?>">
			</label>

			<label>Password:
				<input type="password" name="passvar" value="" placeholder="leave blank to keep current" autocomplete="new-password">
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