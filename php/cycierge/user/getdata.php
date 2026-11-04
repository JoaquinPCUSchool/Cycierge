<?php require_once '/etc/cycierge/config.php';
    	$servername = "localhost";
		$username = DB_USER;
		$password = DB_PASS;
		$dbname = DB_NAME;

        $conn = new mysqli($servername, $username, $password, $dbname);
        // Check connection
        if ($conn->connect_error) {
            die("Connection failed: " . $conn->connect_error);
        }
        $sql = "SELECT ID, USERBATT, USERID, USERNAME, USERPHONE, USERDATE, USERTIME, USERCAM, USERLOCK FROM TBLUSER";
        $result = $conn->query($sql);

        $rows = array();
        if ($result->num_rows > 0) {
            while($row = $result->fetch_assoc()) {
                $rows[] = $row;
            }
        }

        print json_encode($rows);

?>