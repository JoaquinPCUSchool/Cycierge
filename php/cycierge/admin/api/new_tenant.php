<?php require __DIR__ . '/_boot.php'; need_admin();
require_once __DIR__ . '/../../reportlib.php';
// Android "New tenant": check a new tenant in (restarts "time stayed"). POST JSON {room, name, userid, password} - all required.
$b = body(); $room = (int)($b['room'] ?? 0);
$name = trim((string)($b['name'] ?? '')); $uid = trim((string)($b['userid'] ?? '')); $pass = (string)($b['password'] ?? '');
if ($room < 1 || $name === '' || $uid === '' || $pass === '') { http_response_code(400); exit('{"error":"name, username and password are required"}'); }
$c = db();
try { report_new_tenant($c, $room, $name, $uid, $pass); }
catch (Throwable $e) { error_log("new_tenant: " . $e->getMessage()); http_response_code(500); exit('{"error":"save failed"}'); }
echo '{"ok":true}';
