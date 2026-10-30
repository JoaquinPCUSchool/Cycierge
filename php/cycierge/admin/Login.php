<?php
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

			if ($uname == "Admin" and $upass =="Admin" ) {
				$_SESSION["adminid"] = "Admin";
				header('Location: admin.php');
				exit;
			}
			else {
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