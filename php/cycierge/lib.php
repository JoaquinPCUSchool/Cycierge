<?php require_once '/etc/cycierge/config.php';
// Shared helpers for the machine endpoints.
function db() {
    $conn = new mysqli("localhost", DB_USER, DB_PASS, DB_NAME);
    if ($conn->connect_error) { http_response_code(500); exit("Connection failed"); }
    return $conn;
}
// Main.py wraps values in single quotes ('1'); accept both forms.
function arg($k) {
    if (!isset($_GET[$k])) { http_response_code(400); exit("Missing " . $k); }
    return preg_match("/^'(.*)'$/s", $_GET[$k], $m) ? $m[1] : $_GET[$k];
}
