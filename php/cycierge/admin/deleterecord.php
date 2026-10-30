<?php
	$servername="localhost";
	$username="USER";
	$password="12345678";
	$dbname="MYDB";

	// Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }
    
    // sql to delete a record
    $sql = "DELETE FROM TBLRECORD WHERE RECORDID=" .$_GET["RECORDID"]. ";";
    
    if ($conn->query($sql) === TRUE) {
        echo "Record deleted successfully";
    } else {
        echo "Error deleting record: " . $conn->error;
    }
    
    $conn->close();
?>