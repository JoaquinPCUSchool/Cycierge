<?php
require __DIR__ . '/../lib.php';
$vals = [arg("RECORDID"), arg("DT")];
$conn = db();
$stmt = $conn->prepare("INSERT INTO TBLRECORD (RECORDID, DT) VALUES (?, ?)");
echo $stmt->execute($vals) ? "New record created successfully" : "Error: " . $stmt->error;
$conn->close();
