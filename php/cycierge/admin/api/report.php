<?php require __DIR__ . '/_boot.php'; need_admin();
require_once __DIR__ . '/../../reportlib.php';
// GET ?period=week|month|year&date=YYYY-MM-DD (date optional = today)
$c = db();
report_prepare($c);
report_rollup($c);
echo json_encode(report_summary($c, (string)($_GET['period'] ?? 'week'), $_GET['date'] ?? null));
