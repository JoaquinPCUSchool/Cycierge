<?php
// Shared by user.php and logs.php (tenant side only).
function cy_h($s) { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }

// Turn the raw LOGSACTIVITY text into a friendly label + icon kind.
// Raw values in the DB: "User8 Unlock Door", "Admin Unlock Door 2", ...
function cy_activity($raw) {
	$raw = trim((string)$raw);
	if (stripos($raw, 'Admin') === 0 && stripos($raw, 'Unlock') !== false) return ['Door unlocked by admin', 'admin'];
	if (stripos($raw, 'Unlock') !== false)                                  return ['You unlocked the door', 'unlock'];
	return [$raw === '' ? 'Activity' : $raw, 'other'];
}

// "Today, 3:42 PM" / "Yesterday, 9:10 AM" / "Nov 4, 2026, 7:05 PM" (Asia/Manila)
function cy_when($date, $time) {
	try {
		$tz = new DateTimeZone('Asia/Manila');
		$dt = new DateTime($date . ' ' . $time, $tz);
		$today = new DateTime('today', $tz);
		$days = (int)$today->diff(new DateTime($dt->format('Y-m-d'), $tz))->format('%r%a');
		$t = $dt->format('g:i A');
		if ($days === 0)  return "Today, $t";
		if ($days === -1) return "Yesterday, $t";
		return $dt->format('M j, Y') . ", $t";
	} catch (Exception $e) { return trim($date . ' ' . $time); }
}
