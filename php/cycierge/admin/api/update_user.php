<?php require __DIR__ . '/_boot.php'; need_admin();
$b = body(); $id = (int)($b['room'] ?? 0);
$name = (string)($b['name'] ?? ''); $uid = (string)($b['userid'] ?? ''); $pass = (string)($b['password'] ?? '');
$hash = ($pass === '') ? null : password_hash($pass, PASSWORD_DEFAULT);
$c = db(); $s = $c->prepare("UPDATE TBLUSER SET USERNAME = ?, USERID = ?, USERPASS = COALESCE(?, USERPASS) WHERE ID = ?");
$s->bind_param("sssi", $name, $uid, $hash, $id);
$s->execute();
echo '{"ok":true}';
