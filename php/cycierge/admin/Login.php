<?php require_once __DIR__ . '/../throttle.php'; require_once '/etc/cycierge/config.php';
   session_start();
   $_SESSION["adminid"] = "";
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

			if (login_blocked($uname)) {
				echo '<script type="text/javascript"> alert("Too many failed attempts. Try again in 10 minutes."); </script>';
			} elseif (hash_equals(ADMIN_USER, (string)$uname) && password_verify((string)$upass, ADMIN_HASH)) {
				login_ok($uname);
				session_regenerate_id(true);
				$_SESSION["adminid"] = "Admin";
				header('Location: admin.php');
				exit;
			}
			else {
				login_failed($uname);
				echo '<script type="text/javascript"> myFunction(); </script>';
			}		
			
		}
	?>



	<div class="main">

		<h1>CyCierge</h1>
        <h3>Enter Admin credentials</h3>


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