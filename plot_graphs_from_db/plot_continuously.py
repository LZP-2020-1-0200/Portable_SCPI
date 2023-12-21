import mysql.connector
import matplotlib.pyplot as plt
from subprocess import check_output
import time


mydb = mysql.connector.connect(
    host="bat_db_host",
    user="user",
    password="**********",
    database="db"
)
mydb.autocommit = True

mycursor = mydb.cursor(dictionary=True)

fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(2, 2)
ax = (ax0, ax1, ax2, ax3)

lines = []
plt.ion()
plt.show()


run_once = True
history_hours = 10
history_samples = history_hours * 720

while True:

    mycursor.execute("""SELECT
                    id,uuid,sw_ver,name,created,last_update,created_IP,last_update_IP,enabled,data_table
                    FROM systems
                    ORDER BY last_update DESC
                    LIMIT 4""")

    for cols in mycursor.description:
        print(cols[0])

    #data_tables = []
    # for systems in mycursor.fetchall():
    #    data_tables.append(systems[9])
    systems_fetch = mycursor.fetchall()
    ids = []
    systems = {}

    for sys in systems_fetch:
        id = sys['id']
        print(f"id={id} last_update={sys['last_update']}")
        ids.append(id)
        systems[id] = {'name': sys['name'], 'data_table': sys['data_table']}

    ids.sort()
    print(ids)
    # systems.sort()
    # print(systems)

    n = 0
    for id in ids:
        print(systems[id])

        data_table = systems[id]['data_table']
        mycursor.execute(f"""SELECT
                        srv_ts,dev_ts,uptime,sample_n,series,voltage,temperature,RSSI,charge,capacity,full_cap
                        FROM {data_table}
                        ORDER BY dev_ts DESC
                        LIMIT {history_samples}""")

       # for cols in mycursor.description:
       #     print(cols[0])

        data_fetch = mycursor.fetchall()
        dev_ts = []
        voltage = []
        #start_time = data_fetch[-1]['dev_ts']
        end_time = data_fetch[0]['dev_ts']
        hours = []
        for row in data_fetch:
            dev_ts.append(row['dev_ts'])
            voltage.append(row['voltage'])
            hours.append((row['dev_ts']-end_time).total_seconds()/3600+history_hours)

        if run_once:
            line, = ax[n].plot(hours, voltage)
            print(line)
            lines.append(line)
            ax[n].title.set_text(systems[id]['name'])
            ax[n].set_xlabel('time, h')
            ax[n].set_ylabel('voltage, V')
            ax[n].grid()
            ax[n].set_xlim([0, history_hours])
            ax[n].set_ylim([2.9, 4.3])
        else:

            lines[n].set_xdata(hours)
            lines[n].set_ydata(voltage)

        n += 1

    # fig.suptitle(sys['last_update'])
    if run_once:
        plt.tight_layout()

    fig.canvas.draw()
    # plt.savefig("history.pdf")
    # plt.close()
    #check_output(f"move history.pdf histo4.pdf", shell=True).decode()
    fig.canvas.flush_events()
    time.sleep(5)
    run_once = False
