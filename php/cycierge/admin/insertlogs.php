<?php
	$servername="localhost";
	$username="USER";
	$password="12345678";
	$dbname="MYDB";

	$conn = new mysqli($servername, $username, $password, $dbname);
	
	// Check connection
	if ($conn->connect_error) {
	    die("Connection failed: " . $conn->connect_error);
	} 
	
	$sql = "INSERT INTO TBLRECORD(RECORDID, DT)
	VALUES (
	".$_GET["RECORDID"].",
	".$_GET["DT"]."
	)";
	
	if ($conn->query($sql) === TRUE) {
	    echo "New record created successfully";
	} else {
	    echo "Error: " . $sql . "<br>" . $conn->error;
	}
	
	$conn->close();
?>