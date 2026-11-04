<?php require __DIR__ . '/_boot.php';
$b = body(); $u = (string)($b['username'] ?? ''); $p = (string)($b['password'] ?? '');
if (login_blocked($u)) { http_response_code(429); exit('{"error":"blocked"}'); }
if (hash_equals(ADMIN_USER, $u) && password_verify($p, ADMIN_HASH)) {
    login_ok($u); session_regenerate_id(true); $_SESSION['adminid'] = 'Admin';
    exit('{"ok":true}');
}
login_failed($u); http_response_code(401); echo '{"error":"bad_credentials"}';
