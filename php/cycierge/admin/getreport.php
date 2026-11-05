<?php
require_once __DIR__ . '/../reportlib.php';
report_local_only();
header('Content-Type: application/json');
// GET ?period=week|month|year&date=YYYY-MM-DD (date optional = today)
$c = db();
report_prepare($c);
report_rollup($c);
echo json_encode(report_summary($c, (string)($_GET['period'] ?? 'week'), $_GET['date'] ?? null));
