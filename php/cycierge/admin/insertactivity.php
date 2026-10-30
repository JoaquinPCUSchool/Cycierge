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
	
	$sql = "INSERT INTO TBLLOGS(LOGSID, LOGSDATE, LOGSTIME, LOGSACTIVITY)
	VALUES (
	".$_GET["LOGSID"].",
	".$_GET["LOGSDATE"].",
	".$_GET["LOGSTIME"].",
	".$_GET["LOGSACTIVITY"]."
	)";
	
	if ($conn->query($sql) === TRUE) {
	    echo "New record created successfully";
	} else {
	    echo "Error: " . $sql . "<br>" . $conn->error;
	}
	
	$conn->close();
?>