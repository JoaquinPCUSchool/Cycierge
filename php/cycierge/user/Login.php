<?php require_once __DIR__ . '/../throttle.php'; require_once '/etc/cycierge/config.php';
session_start();
$_SESSION["userid"] = "";
$_SESSION["usernum"] = "";
$error = "";

if (isset($_POST['usernamevar'])) {
	$uname = $_POST['usernamevar'];
	$upass = $_POST['userpassvar'];

	if (login_blocked($uname)) {
		$error = "Too many failed attempts. Try again in 10 minutes.";
	} else {
		$conn = new mysqli("localhost", DB_USER, DB_PASS, DB_NAME);
		if ($conn->connect_error) { die("Connection failed: " . $conn->connect_error); }

		$result = $conn->query("SELECT ID, USERID, USERPASS FROM TBLUSER");
		while ($row = $result->fetch_assoc()) {
			// Same check the Pi already used: hashed password + constant-time username compare
			if (hash_equals((string)$row["USERID"], (string)$uname) && password_verify((string)$upass, (string)$row["USERPASS"])) {
				session_regenerate_id(true);
				$_SESSION["userid"]  = $uname;
				$_SESSION["usernum"] = (string)$row["ID"];
				login_ok($uname);
				header('Location: user.php');
				exit;
			}
		}
		login_failed($uname);
		$error = "Username or password is incorrect.";
		$conn->close();
	}
}
?>
<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Login | CyCierge</title>
	<link rel="stylesheet" href="style.css">
</head>
<body>
	<div class="login">
		<h1 class="brand">CyCierge</h1>
		<p class="tag">Security made smart</p>
		<div class="rule"></div>

		<h2>Tenant Login</h2>
		<?php if ($error) { echo '<div class="err">' . htmlspecialchars($error) . '</div>'; } ?>

		<form method="POST" action="#" id="f">
			<label for="u">Username</label>
			<input id="u" type="text" name="usernamevar" required autocomplete="username"
			       value="<?php echo htmlspecialchars($_POST['usernamevar'] ?? '', ENT_QUOTES); ?>">

			<label for="p">Password</label>
			<input id="p" type="password" name="userpassvar" required autocomplete="current-password">

			<label class="remember"><input type="checkbox" id="rem"> Remember me</label>
			<button class="pill" type="submit">Log in</button>
		</form>
	</div>

	<script>
		// "Remember me" stores the username only (never the password).
		var u = document.getElementById('u'), rem = document.getElementById('rem');
		try {
			var saved = localStorage.getItem('cy_user');
			if (saved && !u.value) { u.value = saved; }
			rem.checked = !!saved;
		} catch (e) {}
		document.getElementById('f').addEventListener('submit', function () {
			try { rem.checked ? localStorage.setItem('cy_user', u.value) : localStorage.removeItem('cy_user'); } catch (e) {}
		});
	</script>
</body>
</html>
