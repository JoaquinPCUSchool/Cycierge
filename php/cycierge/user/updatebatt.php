
<?php
header('Content-Type: application/json');

$data = json_decode(file_get_contents("php://input"), true);

$conn = new mysqli("localhost", "USER", "12345678", "MYDB");

if ($conn->connect_error) {
    die(json_encode(["success" => false, "message" => "DB connection failed"]));
}

$id = (int)$data["ID"];
$batt = $conn->real_escape_string($data["USERBATT"]);

$sql = "UPDATE TBLUSER SET USERBATT='$batt' WHERE ID=$id";

if ($conn->query($sql)) {
    echo json_encode(["success" => true, "message" => "Updated"]);
} else {
    echo json_encode(["success" => false, "message" => $conn->error]);
}

$conn->close();
?>