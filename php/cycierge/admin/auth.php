<?php
// Server-side guard: stop here unless logged in.
require_once __DIR__ . '/../lib.php';
session_start();
if (!admin_session_ok()) {
    header("Location: Login.php");
    exit;
}
