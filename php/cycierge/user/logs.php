<?php require_once '/etc/cycierge/config.php';
require __DIR__ . '/auth.php';   // session guard (same as user.php)
require_once __DIR__ . '/_helpers.php';

$uid  = (int)$_SESSION["usernum"];
$conn = new mysqli("localhost", DB_USER, DB_PASS, DB_NAME);
if ($conn->connect_error) { die("Connection failed: " . $conn->connect_error); }

// Logs for THIS room only, newest first
$lid = (string)$uid;
$stmt = $conn->prepare("SELECT LOGSDATE, LOGSTIME, LOGSACTIVITY FROM TBLLOGS WHERE LOGSID = ? ORDER BY LOGSDATE DESC, LOGSTIME DESC LIMIT 50");
$stmt->bind_param("s", $lid);
$stmt->execute();
$logs = $stmt->get_result();
$conn->close();
?>
<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta name="theme-color" content="#0b1f3a">
	<title>Room | <?php echo $uid; ?> (Logs)</title>
	<link rel="stylesheet" href="style.css">
</head>
<body class="top">
<div class="app">
	<div class="bar">
		<a class="backlink" href="user.php" aria-label="Back">
			<svg class="ic" viewBox="0 0 24 24"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>
		</a>
		<div class="wordmark sm"><span>Cy</span>Cierge</div>
	</div>

	<div class="page">
		<div class="hero">
			<small>Room no. <?php echo $uid; ?></small>
			<h1>Latest <em>logs</em></h1>
		</div>

		<div class="loglist">
			<?php if ($logs->num_rows === 0) { echo '<div class="empty">No activity yet.</div>'; } ?>
			<?php while ($r = $logs->fetch_assoc()) { list($txt, $kind) = cy_activity($r["LOGSACTIVITY"]); ?>
				<div class="log <?php echo $kind; ?>">
					<span class="dot"><svg class="ic" viewBox="0 0 24 24">
						<?php if ($kind === 'admin') { ?><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>
						<?php } else { ?><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 7.5-2"/><?php } ?>
					</svg></span>
					<div><b><?php echo cy_h($txt); ?></b><span><?php echo cy_h(cy_when($r["LOGSDATE"], $r["LOGSTIME"])); ?></span></div>
				</div>
			<?php } ?>
		</div>

		<a class="pill ghost" href="user.php">Back to room</a>
		<?php include __DIR__ . '/_foot.php'; ?>
	</div>
</div>
</body>
</html>
