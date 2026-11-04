<?php
require __DIR__ . '/../lib.php';
$rid  = arg("RECORDID");
$conn = db();
$stmt = $conn->prepare("DELETE FROM TBLRECORD WHERE RECORDID = ?");
echo $stmt->execute([$rid]) ? "Record deleted successfully" : "Error deleting record: " . $stmt->error;
$conn->close();
