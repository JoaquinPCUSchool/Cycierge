<?php
// Snapshot proxy: serves one JPEG from a camera board, only to logged-in users.
require_once '/etc/cycierge/config.php';
require_once __DIR__ . '/lib.php';
session_start();
$room = is_string($_GET['room'] ?? null) ? $_GET['room'] : '';
$who  = is_string($_GET['who'] ?? null) ? $_GET['who'] : '';
$ok = false;
if ($who === 'admin' && admin_session_ok()) {
    $ok = true;
} elseif (!empty($_SESSION['userid']) && $who === 'tenant' && ($_SESSION['usernum'] ?? '') === $room) {
    $ok = true;
}
session_write_close();   // don't hold the session lock while fetching
$map = CAM_MAP;
if (!$ok || !isset($map[$room][$who])) { http_response_code(403); exit; }

$ctx = stream_context_create(['http' => ['timeout' => 4]]);
$img = @file_get_contents('http://' . $map[$room][$who] . '/jpg', false, $ctx);
if ($img === false || substr($img, 0, 2) !== "\xFF\xD8") { http_response_code(503); exit; }
header('Content-Type: image/jpeg');
header('Cache-Control: no-store');
echo $img;
