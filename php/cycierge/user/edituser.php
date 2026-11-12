<?php
// Pi dashboard "Edit tenant". Same rules as admin/api/update_user.php (Android admin app):
// name + username are saved, the password only changes when a new one is sent.
// Loopback only (like admin/getreport.php); POST JSON {room, name, userid, password}.
require_once __DIR__ . '/../reportlib.php';   // db(), report_local_only()
report_local_only();
header('Content-Type: application/json');

$b    = json_decode(file_get_contents('php://input'), true) ?: [];
$room = (int)($b['room'] ?? 0);
$name = trim((string)($b['name'] ?? ''));
$uid  = trim((string)($b['userid'] ?? ''));
$pass = (string)($b['password'] ?? '');

if ($room < 1 || $name === '' || $uid === '') {
    http_response_code(400);
    exit('{"error":"name and username are required"}');
}

$hash = ($pass === '') ? null : password_hash($pass, PASSWORD_DEFAULT);
$c = db();
$s = $c->prepare("UPDATE TBLUSER SET USERNAME = ?, USERID = ?, USERPASS = COALESCE(?, USERPASS) WHERE ID = ?");
$s->bind_param("sssi", $name, $uid, $hash, $room);
if (!$s->execute()) {
    error_log("edituser: " . $s->error);
    http_response_code(500);
    exit('{"error":"save failed"}');
}
echo '{"ok":true}';
$c->close();
