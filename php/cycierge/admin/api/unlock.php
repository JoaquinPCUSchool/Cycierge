<?php require __DIR__ . '/_boot.php'; need_admin();
$id = (int)(body()['room'] ?? 0);
if ($id < 1 || $id > 2) { http_response_code(400); exit('{"error":"room"}'); }
$c = db(); $now = new DateTime('now', new DateTimeZone('Asia/Manila'));
$c->prepare("UPDATE TBLUSER SET USERLOCK = 1 WHERE ID = ?")->execute([$id]);
$c->prepare("INSERT INTO TBLLOGS (LOGSID, LOGSDATE, LOGSTIME, LOGSACTIVITY) VALUES (?,?,?,?)")
  ->execute([$id, $now->format('Y-m-d'), $now->format('H:i:s'), 'Admin Unlock Door']);
echo '{"ok":true}';
