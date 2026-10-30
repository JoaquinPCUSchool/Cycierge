<?php
	$servername="localhost";
	$username="USER";
	$password="12345678";
	$dbname="MYDB";
	
	$conn = new mysqli($servername, $username, $password, $dbname);
	
	if ($conn->connect_error) {
		die("Connection failed : " .$conn->connect_error);
	}

	$sql = "UPDATE TBLUSER SET  
		USERLOCK=" .$_GET["USERLOCK"]. " 
		WHERE ID=" .$_GET["ID"]. " ;";
       
	if ($conn->query($sql) === TRUE) {
		echo "Record updated successfully";
		
	} else {
		echo "Error updaterecord: " .$conn->error;
	}
	$conn->close();
?>