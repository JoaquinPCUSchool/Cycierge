
import mysql.connector

# Create connection object
conn = mysql.connector.connect(
    host="localhost",
    user="USER",
    password="12345678",  # Default XAMPP password is usually empty
    database="MYDB"
)

# Create cursor object
cursor = conn.cursor()

# Example: Execute a query
cursor.execute("SELECT * FROM TBLUSER")

# Fetch and print results
for row in cursor.fetchall():
    print(row)

# Close connections
cursor.close()
conn.close()

print ("done")
