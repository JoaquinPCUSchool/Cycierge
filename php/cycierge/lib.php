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

// ---- Admin account ---------------------------------------------------------------------------
// The admin login lives in the ADMIN_ACCOUNT table once it has been changed from the app. Until then
// (table missing/empty) the values from /etc/cycierge/config.php are used, so existing installs keep
// working and config.php never has to be writable by the web server.
// VER goes up on every change; sessions remember the VER they logged in with, so changing the
// credentials signs out every other device/session.
function admin_creds() {                       // [username, password_hash, ver]
    try {
        $r = db()->query("SELECT USERNAME, PASSHASH, VER FROM ADMIN_ACCOUNT WHERE ID = 1");
        if ($r && ($row = $r->fetch_assoc())) return [$row['USERNAME'], $row['PASSHASH'], (int)$row['VER']];
    } catch (Throwable $e) { /* table not created yet */ }
    return [ADMIN_USER, ADMIN_HASH, 0];
}
function admin_check($user, $pass) {           // current VER on success, null on failure
    [$u, $h, $v] = admin_creds();
    $okU = hash_equals((string)$u, (string)$user);
    $okP = password_verify((string)$pass, (string)$h);   // always run both: no timing hint which half was wrong
    return ($okU && $okP) ? $v : null;
}
function admin_login_session($ver) {
    session_regenerate_id(true);
    $_SESSION['adminid'] = 'Admin';
    $_SESSION['credver'] = $ver;
}
function admin_session_ok() {
    return !empty($_SESSION['adminid']) && (int)($_SESSION['credver'] ?? 0) === admin_creds()[2];
}
function admin_set_creds($user, $hash) {       // returns the new VER
    $c = db();
    $c->query("CREATE TABLE IF NOT EXISTS ADMIN_ACCOUNT (
        ID TINYINT NOT NULL PRIMARY KEY,
        USERNAME VARCHAR(32) NOT NULL,
        PASSHASH VARCHAR(255) NOT NULL,
        VER INT NOT NULL DEFAULT 1,
        UPDATED TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )");
    $s = $c->prepare("INSERT INTO ADMIN_ACCOUNT (ID, USERNAME, PASSHASH, VER) VALUES (1, ?, ?, 1)
                      ON DUPLICATE KEY UPDATE USERNAME = VALUES(USERNAME), PASSHASH = VALUES(PASSHASH), VER = VER + 1");
    $s->bind_param('ss', $user, $hash);
    $s->execute();
    return admin_creds()[2];
}
