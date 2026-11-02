<?php
require __DIR__ . '/../lib.php';
$vals = [arg("USERID"), arg("USERPASS"), arg("USERNAME"), arg("USERPHONE"), arg("USERDATE"), arg("USERTIME"), (int) arg("ID")];
$conn = db();
$stmt = $conn->prepare("UPDATE TBLUSER SET USERID = ?, USERPASS = ?, USERNAME = ?, USERPHONE = ?, USERDATE = ?, USERTIME = ? WHERE ID = ?");
echo $stmt->execute($vals) ? "Record updated successfully" : "Error updaterecord: " . $stmt->error;
$conn->close();
