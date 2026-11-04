<?php require __DIR__ . '/_boot.php'; need_admin();
$room = (int)(body()['room'] ?? 0);
if ($room < 1) { http_response_code(400); exit('{"error":"room"}'); }
db()->prepare("DELETE FROM TBLLOGS WHERE LOGSID = ?")->execute([$room]);
echo '{"ok":true}';
