<?php require __DIR__ . '/_boot.php'; need_admin();
$room = (int)($_GET['room'] ?? 0);
$s = db()->prepare("SELECT LOGSDATE, LOGSTIME, LOGSACTIVITY FROM TBLLOGS WHERE LOGSID = ? ORDER BY LOGSDATE DESC, LOGSTIME DESC");
$s->execute([$room]);
echo json_encode($s->get_result()->fetch_all(MYSQLI_ASSOC));
