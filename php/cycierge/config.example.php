<?php
// Copy to /etc/cycierge/config.php (outside the web root) and fill in real values.
define('DB_HOST', 'localhost');
define('DB_USER', 'cycierge_app');
define('DB_PASS', 'change-me');
define('DB_NAME', 'MYDB');
define('ADMIN_USER', 'Admin');
define('ADMIN_HASH', '');   // php -r 'echo password_hash("yourpass", PASSWORD_DEFAULT);'
