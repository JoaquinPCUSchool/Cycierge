<?php
// Server-side guard: stop here unless logged in.
session_start();
if (empty($_SESSION["userid"])) {
    header("Location: Login.php");
    exit;
}
