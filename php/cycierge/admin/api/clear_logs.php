<?php require __DIR__ . '/_boot.php'; need_admin();
require_once __DIR__ . '/../../reportlib.php';
$room = (int)(body()['room'] ?? 0);
if ($room < 1) { http_response_code(400); exit('{"error":"room"}'); }
$c = db();
report_prepare($c); report_rollup($c);      // keep the history for the reports before the raw rows go
$c->prepare("DELETE FROM TBLLOGS WHERE LOGSID = ?")->execute([$room]);
echo '{"ok":true}';
