<?php require __DIR__ . '/_boot.php';
$b = body(); $u = (string)($b['username'] ?? ''); $p = (string)($b['password'] ?? '');
if (login_blocked($u)) { http_response_code(429); exit('{"error":"blocked"}'); }
if (($ver = admin_check($u, $p)) !== null) {
    login_ok($u); admin_login_session($ver);
    exit('{"ok":true}');
}
login_failed($u); http_response_code(401); echo '{"error":"bad_credentials"}';
