<?php require __DIR__ . '/_boot.php'; need_admin();
$r = db()->query("SELECT ID, USERNAME, USERID, USERDATE, USERTIME, USERBATT, USERLOCK FROM TBLUSER ORDER BY ID");
echo json_encode($r->fetch_all(MYSQLI_ASSOC));
