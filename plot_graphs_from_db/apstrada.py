import mysql.connector
import matplotlib.pyplot as plt
from subprocess import check_output

mydb = mysql.connector.connect(
    host="bat_db_host",
    user="db_user",
    password="************",
    database="bat_db"
)

mycursor = mydb.cursor()

mycursor.execute("""SELECT
                 id,uuid,sw_ver,name,created,last_update,created_IP,last_update_IP,enabled,data_table
                 FROM systems
                 ORDER BY id""")

# for cols in mycursor.description:
#    print(cols[0])

#data_tables = []
# for systems in mycursor.fetchall():
#    data_tables.append(systems[9])
systems = mycursor.fetchall()


for system in systems:
    data_table = system[9]
    print(data_table)
    mycursor.execute(f"""SELECT 
                     srv_ts,dev_ts,uptime,sample_n,series,voltage,temperature,RSSI,charge,capacity,full_cap
                     FROM {data_table}
                    ORDER BY dev_ts""")
    # for cols in mycursor.description:
    # print(cols[0])
    data = mycursor.fetchall()
    series = None
    prev_sample_n = None
    for row in data:
        srv_ts = row[0]
        sample_n = row[3]
        if series is None:
            series = 0
        elif sample_n != prev_sample_n + 1:
            series += 1
            print(series)
        prev_sample_n = sample_n
        mycursor.execute(f"UPDATE {data_table} " +
                         """ SET `series` = %s
                             WHERE `srv_ts` = %s""", (series, srv_ts))
mydb.commit()


figno = 999
for system in systems:
    data_table = system[9]
    system_name = system[3]
    print(data_table)
    mycursor.execute(f"""SELECT DISTINCT series
                     FROM {data_table}
                    ORDER BY series""")
    series_list = mycursor.fetchall()
    print(series_list)
    for ser in series_list:
        series = ser[0]
        if series is None:
            continue
        query = f"""SELECT 
                        srv_ts,dev_ts,uptime,sample_n,series,voltage,temperature,RSSI,charge,capacity,full_cap
                        FROM {data_table} 
                        WHERE `series` = %s
                        ORDER BY dev_ts"""
#        print(query)
#        print(series)
        mycursor.execute(query, [series])
        ser_data = mycursor.fetchall()
        time = []
        voltage = []
        charge = []
        temperature = []
        rssi = []
        start_time = None
        t_for_current = []
        prev_charge = None
        current = []
        for ser_row in ser_data:
            dev_ts = ser_row[1]
            chg = ser_row[8]
            if start_time is None:
                start_time = dev_ts
            else:
                t_for_current.append((dev_ts-start_time).total_seconds()/3600)
                current.append(chg-prev_charge)

            time.append((dev_ts-start_time).total_seconds()/3600)
            voltage.append(ser_row[5])
            temperature.append(ser_row[6])

            charge.append(chg)
            prev_charge = chg
            rssi.append(ser_row[7])

        fig, ((ax_volt, ax_temp), (ax_IV, ax_rssi)) = plt.subplots(2, 2)

        ax2_volt = ax_volt.twinx()
        ax_volt.plot(time, voltage, 'r')
        ax2_volt.plot(time, charge, 'b')

        ax_volt.set_xlabel('time, h')
        ax_volt.set_ylabel('voltage, V', color='r')
        ax2_volt.set_ylabel('charge, binary', color='b')
#        plt.plot()
#        plt.ylabel('some numbers')
        ax2_temp = ax_temp.twinx()
        ax_temp.plot(time, temperature, 'r')
        ax2_temp.plot(time, charge, 'b')

        ax_temp.set_xlabel('time, h')
        ax_temp.set_ylabel('Temperature, ℃', color='r')
        ax2_temp.set_ylabel('charge, binary', color='b')

        ax_rssi.plot(time, rssi, 'r')
        ax_rssi.set_xlabel('time, h')
        ax_rssi.set_ylabel('RSSI, dBm', color='r')

        ax2_IV = ax_IV.twinx()
        ax2_IV.plot(t_for_current, current, 'b')
        ax_IV.plot(time, voltage, 'r')

        ax_IV.set_xlabel('time, h')
        ax_IV.set_ylabel('voltage, V', color='r')
        ax2_IV.set_ylabel('current, binary', color='b')

        fig.suptitle(f"{system_name}, start = {start_time}")
        plt.tight_layout()
        # plt.show()
        figno += 1
        filename = f"bat_{figno}_{data_table}_series_{series}.pdf"
        print(filename)
        plt.savefig(filename)
        plt.close()



check_output(
        f"pdftk bat_1*.pdf cat output prototest.pdf", shell=True).decode()