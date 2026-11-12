<?php
// Pi dashboard "New tenant": check a new tenant in (restarts "time stayed"). Loopback only.
// POST JSON {room, name, userid, password} - all required.
require_once __DIR__ . '/../reportlib.php';   // db(), report_local_only(), report_new_tenant()
report_local_only();
header('Content-Type: application/json');

$b    = json_decode(file_get_contents('php://input'), true) ?: [];
$room = (int)($b['room'] ?? 0);
$name = trim((string)($b['name'] ?? ''));
$uid  = trim((string)($b['userid'] ?? ''));
$pass = (string)($b['password'] ?? '');

if ($room < 1 || $name === '' || $uid === '' || $pass === '') {
    http_response_code(400);
    exit('{"error":"name, username and password are required"}');
}
$c = db();
try { report_new_tenant($c, $room, $name, $uid, $pass); }
catch (Throwable $e) { error_log("newtenant: " . $e->getMessage()); http_response_code(500); exit('{"error":"save failed"}'); }
echo '{"ok":true}';
$c->close();
