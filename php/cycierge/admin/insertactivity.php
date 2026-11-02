<?php
require __DIR__ . '/../lib.php';
$vals = [arg("LOGSID"), arg("LOGSDATE"), arg("LOGSTIME"), arg("LOGSACTIVITY")];
$conn = db();
$stmt = $conn->prepare("INSERT INTO TBLLOGS (LOGSID, LOGSDATE, LOGSTIME, LOGSACTIVITY) VALUES (?, ?, ?, ?)");
echo $stmt->execute($vals) ? "New record created successfully" : "Error: " . $stmt->error;
$conn->close();
