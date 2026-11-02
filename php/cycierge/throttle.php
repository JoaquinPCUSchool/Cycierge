<?php
// Login throttle: max 5 failed attempts per account name per 10 minutes.
require_once '/etc/cycierge/config.php';

function _thr_db() {
    static $c = null;
    if ($c === null) { $c = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME); }
    return $c;
}
function _thr_key($user) { return 'u:' . strtolower(substr((string)$user, 0, 60)); }

function login_blocked($user) {
    $c = _thr_db();
    $c->query("DELETE FROM LOGIN_ATTEMPTS WHERE TS < " . (time() - 600));
    $s = $c->prepare("SELECT COUNT(*) FROM LOGIN_ATTEMPTS WHERE WHO = ? AND TS >= ?");
    $s->execute([_thr_key($user), time() - 600]);
    return (int)$s->get_result()->fetch_row()[0] >= 5;
}
function login_failed($user) {
    $s = _thr_db()->prepare("INSERT INTO LOGIN_ATTEMPTS (WHO, TS) VALUES (?, ?)");
    $s->execute([_thr_key($user), time()]);
}
function login_ok($user) {
    $s = _thr_db()->prepare("DELETE FROM LOGIN_ATTEMPTS WHERE WHO = ?");
    $s->execute([_thr_key($user)]);
}
