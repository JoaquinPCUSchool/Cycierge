<?php
// Server-side guard: stop here unless logged in.
session_start();
if (empty($_SESSION["adminid"])) {
    header("Location: Login.php");
    exit;
}
