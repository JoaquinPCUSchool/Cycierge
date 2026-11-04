<?php
require __DIR__ . '/auth.php';   // Pi's shared session check + DB config constants
$room = (int)$_SESSION["usernum"];
?>
<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Room | <?php echo $room; ?> (Camera)</title>
	<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="live">
	<div class="stage">
		<img id="stream" src="../cam.php?room=<?php echo $room; ?>&amp;who=tenant" alt="Live camera">
		<div class="offline" id="off">Camera unavailable</div>
		<div class="clock" id="clock">HH:MM</div>
		<div class="overlay"><span>Room no. <?php echo $room; ?></span><span id="date">DD/MM/YYYY</span></div>
	</div>
	<div class="foot">
		<button class="back" onclick="goBack()" aria-label="Back">
			<svg class="ic" viewBox="0 0 24 24"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>
		</button>
		CyCierge
	</div>
</div>
<script>
	function tick() {
		var n = new Date();
		document.getElementById('clock').textContent = n.toLocaleTimeString('en-GB', {hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Manila'});
		document.getElementById('date').textContent  = n.toLocaleDateString('en-GB', {timeZone: 'Asia/Manila'});
	}
	tick(); setInterval(tick, 1000);

	// Live view through cam.php: fetch one snapshot, then ask for the next (same loop as before).
	var img = document.getElementById('stream'), off = document.getElementById('off'), alive = true;
	var base = img.getAttribute('src');
	function next() { if (alive) { img.src = base + '&t=' + Date.now(); } }
	img.onload  = function () { off.style.display = 'none'; setTimeout(next, 400); };
	img.onerror = function () { off.style.display = 'flex'; setTimeout(next, 3000); };

	function goBack() {
		alive = false; img.onload = img.onerror = null;
		window.location.href = 'user.php';
	}
</script>
</body>
</html>
