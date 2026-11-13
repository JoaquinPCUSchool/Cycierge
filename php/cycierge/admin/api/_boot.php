<?php
require_once '/etc/cycierge/config.php';
require_once __DIR__ . '/../../throttle.php';
require_once __DIR__ . '/../../lib.php';
session_start();
header('Content-Type: application/json');
function need_admin() {
    if (!admin_session_ok()) { http_response_code(401); exit('{"error":"auth"}'); }
}
function body() { return json_decode(file_get_contents('php://input'), true) ?: []; }
