<?php
require __DIR__ . '/../lib.php';
$pass = arg("USERPASS");
if ($pass === '') { http_response_code(400); exit("Empty password"); }
$vals = [arg("USERID"), password_hash($pass, PASSWORD_DEFAULT), arg("USERNAME"), arg("USERPHONE"), arg("USERDATE"), arg("USERTIME"), (int) arg("ID")];
$conn = db();
$stmt = $conn->prepare("UPDATE TBLUSER SET USERID = ?, USERPASS = ?, USERNAME = ?, USERPHONE = ?, USERDATE = ?, USERTIME = ? WHERE ID = ?");
echo $stmt->execute($vals) ? "Record updated successfully" : "Error updaterecord: " . $stmt->error;
$conn->close();
