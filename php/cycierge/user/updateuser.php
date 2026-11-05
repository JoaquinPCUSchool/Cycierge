<?php
require __DIR__ . '/../lib.php';
require_once __DIR__ . '/../reportlib.php';
$pass = arg("USERPASS");
if ($pass === '') { http_response_code(400); exit("Empty password"); }
$vals = [arg("USERID"), password_hash($pass, PASSWORD_DEFAULT), arg("USERNAME"), arg("USERPHONE"), arg("USERDATE"), arg("USERTIME"), (int) arg("ID")];
$conn = db();
// Reports: make sure the outgoing tenant of this room is in TBLSTAYS before TBLUSER is overwritten.
try { report_prepare($conn); } catch (Throwable $e) { error_log("report_prepare: " . $e->getMessage()); }
$stmt = $conn->prepare("UPDATE TBLUSER SET USERID = ?, USERPASS = ?, USERNAME = ?, USERPHONE = ?, USERDATE = ?, USERTIME = ? WHERE ID = ?");
$ok = $stmt->execute($vals);
if ($ok) {
    try { report_stay_open($conn, (int) arg("ID"), arg("USERNAME"), arg("USERID"), arg("USERDATE"), arg("USERTIME")); }
    catch (Throwable $e) { error_log("report_stay_open: " . $e->getMessage()); }   // never break tenant registration
}
echo $ok ? "Record updated successfully" : "Error updaterecord: " . $stmt->error;
$conn->close();
