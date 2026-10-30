<?php
    	$servername = "localhost";
		$username = "USER";
		$password = "12345678";
		$dbname = "MYDB";

        $conn = new mysqli($servername, $username, $password, $dbname);
        // Check connection
        if ($conn->connect_error) {
            die("Connection failed: " . $conn->connect_error);
        }
        $sql = "SELECT * FROM TBLUSER";
        $result = $conn->query($sql);

        $rows = array();
        if ($result->num_rows > 0) {
            while($row = $result->fetch_assoc()) {
                $rows[] = $row;
            }
        }

        print json_encode($rows);

?>