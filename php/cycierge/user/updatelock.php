
<?php require_once '/etc/cycierge/config.php';
header('Content-Type: application/json');

$data = json_decode(file_get_contents("php://input"), true);

$conn = new mysqli("localhost", DB_USER, DB_PASS, DB_NAME);

if ($conn->connect_error) {
    die(json_encode(["success" => false, "message" => "DB connection failed"]));
}

$id = (int)$data["ID"];
$lock = $conn->real_escape_string($data["USERLOCK"]);

$sql = "UPDATE TBLUSER SET USERLOCK='$lock' WHERE ID=$id";

if ($conn->query($sql)) {
    echo json_encode(["success" => true, "message" => "Updated"]);
} else {
    echo json_encode(["success" => false, "message" => $conn->error]);
}

$conn->close();
?>