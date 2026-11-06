<?php require_once '/etc/cycierge/config.php';
require __DIR__ . '/auth.php';   // Pi's shared session check + DB config constants
require_once __DIR__ . '/_helpers.php';

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

$stmt = $conn->prepare("SELECT USERNAME, USERBATT, USERLOCK, USERDATE, USERTIME FROM TBLUSER WHERE ID = ?");
$stmt->bind_param("i", $uid);
$stmt->execute();
$u = $stmt->get_result()->fetch_assoc() ?: [];

$name      = $u["USERNAME"] ?? "Tenant";
$batt      = max(0, min(100, (int)($u["USERBATT"] ?? 0)));
$unlocking = (($u["USERLOCK"] ?? "0") == "1");   // 1 = unlock requested, ESP32 resets it to 0

// Refresh fast while the door is unlocking so "Unlocking..." clears itself; slow otherwise.
header("Refresh: " . ($unlocking ? 3 : 25));

// Battery colour band: ok / mid / low
$bcls = $batt < 20 ? 'low' : ($batt < 50 ? 'mid' : 'ok');

// Time stayed (counts UP from check-in, as the code always did)
$days = "-"; $rest = "";
try {
	$iv   = (new DateTime(($u["USERDATE"] ?? "") . " " . ($u["USERTIME"] ?? ""), $tz))->diff(new DateTime('now', $tz));
	$days = $iv->days . ($iv->days == 1 ? " day" : " days");
	$rest = $iv->format('%h hr %i min');
} catch (Exception $e) {}

// Most recent log for THIS room (the full list lives on logs.php)
$lid = (string)$uid;
$stmt = $conn->prepare("SELECT LOGSDATE, LOGSTIME, LOGSACTIVITY FROM TBLLOGS WHERE LOGSID = ? ORDER BY LOGSDATE DESC, LOGSTIME DESC LIMIT 1");
$stmt->bind_param("s", $lid);
$stmt->execute();
$last = $stmt->get_result()->fetch_assoc();
$conn->close();
?>
<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta name="theme-color" content="#0b1f3a">
	<title>Room | <?php echo $uid; ?></title>
	<link rel="stylesheet" href="style.css">
</head>
<body class="top">
<div class="app">
	<div class="bar">
		<div class="wordmark sm"><span>Cy</span>Cierge</div>
		<div class="chip batt <?php echo $bcls; ?>" title="Door unit battery">
			<span class="cell"><i style="width:<?php echo $batt; ?>%"></i></span><?php echo $batt; ?>%
		</div>
	</div>

	<div class="page">
		<div class="hero">
			<small>Welcome back</small>
			<h1>Room no. <em><?php echo $uid; ?></em></h1>
		</div>

		<div class="card stay">
			<div class="who">
				<svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-7 8-7s8 3 8 7"/></svg>
				<div><small>Tenant</small><b><?php echo cy_h($name); ?></b></div>
			</div>
			<div class="time"><small>Time stayed</small><b><?php echo cy_h($days); ?></b><small><?php echo cy_h($rest); ?></small></div>
		</div>

		<a class="card action cam" href="camera.php" aria-label="Open live camera">
			<span class="live"><i></i>LIVE</span>
			<svg class="ic big" viewBox="0 0 24 24"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>
			<span class="label">Live camera<small>See who is at your door</small></span>
			<svg class="ic go" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>
		</a>

		<form class="card lockbox<?php echo $unlocking ? ' busy' : ''; ?>" method="POST" action="user.php"
		      onsubmit="return confirm('Unlock the door for Room <?php echo $uid; ?>?');">
			<div class="state">
				<?php if ($unlocking) { ?>
					<svg class="ic" viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 7.5-2"/></svg> Unlocking&hellip;
				<?php } else { ?>
					<svg class="ic" viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg> Door is locked
				<?php } ?>
			</div>
			<button class="pill" type="submit" name="btnunlock" <?php echo $unlocking ? 'disabled' : ''; ?>>
				<svg class="ic" viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 7.5-2"/></svg>
				<?php echo $unlocking ? 'Unlocking&hellip;' : 'Unlock door'; ?>
			</button>
		</form>

		<a class="card row logs" href="logs.php">
			<svg class="ic" viewBox="0 0 24 24"><path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h11"/></svg>
			<span class="label">Latest logs for this unit
				<small><?php
					if ($last) { echo 'Last: ' . cy_h(cy_when($last["LOGSDATE"], $last["LOGSTIME"])); }
					else { echo 'No activity yet'; }
				?></small>
			</span>
			<svg class="ic go" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>
		</a>

		<?php include __DIR__ . '/_foot.php'; ?>
	</div>
</div>
</body>
</html>
