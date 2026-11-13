<?php require __DIR__ . '/_boot.php'; need_admin();
// Android "Admin login": POST JSON {current_password, new_username, new_password}.
// Blank new_username keeps the username, blank new_password keeps the password.
// Also applies to the web admin login (same account).
function cred_fail($code, $key) { http_response_code($code); exit(json_encode(['error' => $key])); }

$b   = body();
$cur = (string)($b['current_password'] ?? '');
$nu  = trim((string)($b['new_username'] ?? ''));
$np  = (string)($b['new_password'] ?? '');

[$u0, $h0] = admin_creds();
if ($nu === '') $nu = $u0;

// Re-check the current password, with the same throttle as login, so a stolen session can't guess it.
if (login_blocked($u0)) cred_fail(429, 'blocked');
if (admin_check($u0, $cur) === null) { login_failed($u0); cred_fail(403, 'wrong_password'); }

if (!preg_match('/^[A-Za-z0-9_.-]{3,32}$/', $nu)) cred_fail(400, 'bad_username');
if ($np !== '') {
    if (strlen($np) < 8)  cred_fail(400, 'weak_password');
    if (strlen($np) > 72) cred_fail(400, 'password_too_long');   // bcrypt only uses the first 72 bytes
    if ($np === $cur)     cred_fail(400, 'same_password');
}
if ($np === '' && $nu === $u0) cred_fail(400, 'nothing_to_change');

$hash = ($np === '') ? $h0 : password_hash($np, PASSWORD_DEFAULT);
try { $ver = admin_set_creds($nu, $hash); }
catch (Throwable $e) { error_log('change_credentials: ' . $e->getMessage()); cred_fail(500, 'save_failed'); }

login_ok($u0); login_ok($nu);
$_SESSION['credver'] = $ver;     // keep THIS session signed in (all others now fail the VER check)
echo json_encode(['ok' => true, 'username' => $nu]);
