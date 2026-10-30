import requests
import json
import time


#data = requests.get("http://iotwebserver.x10host.com/getdata.php")
data = requests.get("http://localhost/cycierge/user/getrecord.php")
#print data.text
parseData = json.loads(data.text)

for row in range(0, len(parseData)):
    print (parseData[row]["ID"])
    print (parseData[row]["DT"])
