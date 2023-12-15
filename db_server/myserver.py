# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
# import cgi
# import time
import mysql.connector


hostName = ""
serverPort = 8080


class MyServer(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(
            bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(
            bytes("<p>This is an example web server.</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

    def do_POST(self):
        global mycursor
        # ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        #        print ("post")
        print(self.headers)

        # <--- Gets the size of data
        content_length = int(self.headers['Content-Length'])
        # <--- Gets the data itself
        post_data = self.rfile.read(content_length)
        # print(post_data)
        message = json.loads(post_data)
        print(message)

        uuid = None
        sw_ver = None
        data_table = None
        timestamp = None
        uptime = None
        sample_n = None
        voltage = None
        RSSI = None
        temperature = None
        charge= None
        capacity= None
        full_cap= None

        for level1 in message.keys():
            print(level1)
            for key in message[level1].keys():
                if level1 == 'system' and key == 'uuid':
                    uuid = message[level1][key]
                elif level1 == 'system' and key == 'sw_ver':
                    sw_ver = message[level1][key]
                elif level1 == 'system' and key == 'timestamp':
                    timestamp = message[level1][key]
                elif level1 == 'system' and key == 'uptime':
                    uptime = message[level1][key]
                elif level1 == 'system' and key == 'sample_n':
                    sample_n = message[level1][key]
                elif level1 == 'system' and key == 'RSSI':
                    RSSI = message[level1][key]
                elif level1 == 'LTC2942' and key == 'voltage':
                    voltage = message[level1][key]
                elif level1 == 'LTC2942' and key == 'temperature':
                    temperature = message[level1][key]
                elif level1 == 'LTC2942' and key == 'charge':
                    charge = message[level1][key]
                elif level1 == 'LTC2942' and key == 'capacity':
                    capacity = message[level1][key]
                elif level1 == 'LTC2942' and key == 'full_cap':
                    full_cap = message[level1][key]


                else:
                    print(f"\t{key}")

        mycursor.execute("""UPDATE systems
                         SET `last_update` = NOW(), `last_update_IP` = %s
                         WHERE `uuid` = %s""", (self.address_string(), uuid))

        if mycursor.rowcount == 0:
            query = """INSERT INTO `systems`
                (`uuid`, `sw_ver`, `last_update`, `created_IP`, `last_update_IP`)
                VALUES (%s, %s,  NOW(), %s, %s)"""
            tuple1 = (uuid, sw_ver, self.address_string(),
                      self.address_string())
            mycursor.execute(query, tuple1)

        mycursor.execute("""SELECT data_table FROM `systems`
                      WHERE `uuid` = %s AND `enabled` = 1 """, [uuid])
        for rez in mycursor.fetchall():
            data_table = rez[0]
        print(data_table)

        if data_table is not None:
            mycursor.execute(f"""CREATE TABLE IF NOT EXISTS {data_table} (
                             `srv_ts` timestamp PRIMARY KEY DEFAULT CURRENT_TIMESTAMP,
                             `dev_ts` timestamp NOT NULL,
                             `uptime` int UNSIGNED NOT NULL,
                             `sample_n` int UNSIGNED NOT NULL,
                             `series` int UNSIGNED NULL,
                             `voltage` float NOT NULL,
                             `temperature` float NOT NULL,
                             `RSSI` float NOT NULL,
                             `charge` float NOT NULL,
                             `capacity` float NOT NULL,
                             `full_cap` float NOT NULL,
                             `post` json NOT NULL
                              )""")
            mycursor.execute(f"INSERT INTO {data_table} " +
                             """(`dev_ts`, `uptime`, `sample_n`, `voltage`, `temperature`, `RSSI`, `charge`, `capacity`, `full_cap`, `post`)
                             VALUES (FROM_UNIXTIME(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                             (timestamp, uptime, sample_n, voltage, temperature, RSSI, charge, capacity, full_cap, post_data))


# INSERT INTO `systems` (`id`, `created`, `created_IP`, `enabled`, `data_table`) VALUES ('sss', CURRENT_TIMESTAMP, 'rrrr', '0', 'ffff'), ('1', CURRENT_TIMESTAMP, 'ddd', '0', '1');

#        mycursor.execute(
#            f"CREATE TABLE IF NOT EXISTS `{table_name}` (name VARCHAR(255), address VARCHAR(255))")
#        print(self.address_string())

#        message["received"] = 1


#        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data

#        post_data = self.rfile.read(content_length) # <--- Gets the data itself
#        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
#                str(self.path), str(self.headers), post_data.decode('utf-8'))

        # refuse to receive non-json content
        # if ctype != 'application/json':
        #    self.send_response(400)
        #    self.end_headers()
        #    return

        # read the message and convert it into a python dictionary
#        print (self)
#        length = int(self.headers.getheader('content-length'))
#        message = json.loads(self.rfile.read(length))

        # add a property to the object, just to mess with data
#        message['received'] = 'ok'
#        message={"status":"test"}

        # send the message back
#        self._set_headers()
#        self.wfile.write(json.dumps(message))
#        self.send_response(200)
#        self.send_header("Content-type", "text/html")
#        self.end_headers()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(message), "utf-8"))


if __name__ == "__main__":
    mydb = mysql.connector.connect(
        host="localhost",
        user="db_user",
        password="************",
        database="bat_db"
    )
    mydb.autocommit = True

    mydb.time_zone = '+00:00'
    print(mydb.time_zone)

    mycursor = mydb.cursor()

    mycursor.execute("""CREATE TABLE IF NOT EXISTS systems (
                     id int UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
                     uuid varchar(255) UNIQUE NOT NULL,
                     sw_ver varchar(255) NOT NULL,
                     name varchar(255) NOT NULL DEFAULT 'nosaukums',
                     created timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                     last_update timestamp NOT NULL,
                     created_IP varchar(255) NOT NULL,
                     last_update_IP varchar(255) NOT NULL,
                     enabled tinyint(1) NOT NULL DEFAULT '0',
                     data_table varchar(255) UNIQUE NULL
)""")

    mycursor.execute("SHOW TABLES")

    for x in mycursor:
        print(x)

    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
