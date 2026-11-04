<?php require_once '/etc/cycierge/config.php';
require __DIR__ . '/auth.php';   // Pi's shared session check + DB config constants
function cy_h($s) { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }

$tz  = new DateTimeZone('Asia/Manila');
$uid = (int)$_SESSION["usernum"];

$conn = new mysqli("localhost", DB_USER, DB_PASS, DB_NAME);
if ($conn->connect_error) { die("Connection failed: " . $conn->connect_error); }

// Unlock: same DB writes as before, then redirect so a page refresh can't re-unlock / double-log.
if (isset($_POST['btnunlock'])) {
	$now = new DateTime('now', $tz);
	$d = $now->format('Y-m-d');
	$t = $now->format('H:i:s');
	$lid = (string)$uid;
	$act = "User" . $uid . " Unlock Door";

	$stmt = $conn->prepare("UPDATE TBLUSER SET USERLOCK = '1' WHERE ID = ?");
	$stmt->bind_param("i", $uid);
	$stmt->execute();

	$stmt = $conn->prepare("INSERT INTO TBLLOGS (LOGSID, LOGSDATE, LOGSTIME, LOGSACTIVITY) VALUES (?, ?, ?, ?)");
	$stmt->bind_param("ssss", $lid, $d, $t, $act);
	$stmt->execute();
	header('Location: user.php');
	exit;
}
header("Refresh: 25");

$stmt = $conn->prepare("SELECT USERNAME, USERBATT, USERLOCK, USERDATE, USERTIME FROM TBLUSER WHERE ID = ?");
$stmt->bind_param("i", $uid);
$stmt->execute();
$u = $stmt->get_result()->fetch_assoc() ?: [];

$name      = $u["USERNAME"] ?? "Tenant";
$batt      = max(0, min(100, (int)($u["USERBATT"] ?? 0)));
$unlocking = (($u["USERLOCK"] ?? "0") == "1");   // 1 = unlock requested, ESP32 resets it to 0

// Time stayed (counts UP from check-in, as the code always did)
$days = "-"; $rest = "";
try {
	$iv   = (new DateTime(($u["USERDATE"] ?? "") . " " . ($u["USERTIME"] ?? ""), $tz))->diff(new DateTime('now', $tz));
	$days = $iv->days . ($iv->days == 1 ? " day" : " days");
	$rest = $iv->format('%h hr %i min');
} catch (Exception $e) {}

// Logs for THIS room only, newest first
$lid = (string)$uid;
$stmt = $conn->prepare("SELECT LOGSDATE, LOGSTIME, LOGSACTIVITY FROM TBLLOGS WHERE LOGSID = ? ORDER BY LOGSDATE DESC, LOGSTIME DESC LIMIT 30");
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
	<title>Room | <?php echo $uid; ?></title>
	<link rel="stylesheet" href="style.css">
</head>
<body class="top">
<div class="app">
	<div class="bar">CyCierge</div>
	<div class="page">
		<h1>Room no. <?php echo $uid; ?></h1>

		<div class="grid">
			<div class="tile">
				<div class="who">
					<svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-7 8-7s8 3 8 7"/></svg>
					<?php echo cy_h($name); ?>
				</div>
				<div class="stay"><small>Time stayed</small><b><?php echo cy_h($days); ?></b><small><?php echo cy_h($rest); ?></small></div>
			</div>

			<a class="tile cam" href="camera.php" aria-label="View camera">
				<svg class="ic big" viewBox="0 0 24 24"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>
			</a>

			<form class="tile lock" method="POST" action="user.php">
				<div class="state">
					<?php if ($unlocking) { ?>
						<svg class="ic" viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 7.5-2"/></svg> Unlocking...
					<?php } else { ?>
						<svg class="ic" viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg> Locked
					<?php } ?>
				</div>
				<button class="pill" type="submit" name="btnunlock" <?php echo $unlocking ? 'disabled' : ''; ?>>Unlock</button>
			</form>

			<div class="tile batt">
				<div>Battery<br>Percentage<b><?php echo $batt; ?> %</b></div>
				<div class="cell<?php echo $batt < 20 ? ' low' : ''; ?>"><i style="height:<?php echo $batt; ?>%"></i></div>
			</div>
		</div>

		<div class="logs">
			<h2>Latest logs for this unit</h2>
			<div class="loglist">
				<?php if ($logs->num_rows === 0) { echo '<div class="empty">No activity yet.</div>'; } ?>
				<?php while ($r = $logs->fetch_assoc()) { ?>
					<div class="log"><b><?php echo cy_h($r["LOGSACTIVITY"]); ?></b><span><?php echo cy_h($r["LOGSDATE"]) . " &middot; " . cy_h($r["LOGSTIME"]); ?></span></div>
				<?php } ?>
			</div>
		</div>
	</div>
</div>
</body>
</html>
