<?php
require __DIR__ . '/../lib.php';
$lock = (int) arg("USERLOCK") === 1 ? 1 : 0;
$id   = (int) arg("ID");
$conn = db();
$stmt = $conn->prepare("UPDATE TBLUSER SET USERLOCK = ? WHERE ID = ?");
echo $stmt->execute([$lock, $id]) ? "Record updated successfully" : "Error updaterecord: " . $stmt->error;
$conn->close();
