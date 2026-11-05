<?php
require __DIR__ . '/../lib.php';
require_once __DIR__ . '/../reportlib.php';
$rid  = arg("RECORDID");
$conn = db();
report_prepare($conn); report_rollup($conn);   // keep the history for the reports before the raw rows go
$stmt = $conn->prepare("DELETE FROM TBLRECORD WHERE RECORDID = ?");
echo $stmt->execute([$rid]) ? "Record deleted successfully" : "Error deleting record: " . $stmt->error;
$conn->close();
