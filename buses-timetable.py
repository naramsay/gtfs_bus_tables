#!/usr/bin/python

import requests
import zipfile
import mysql.connector
from mysql.connector.constants import ClientFlag
from datetime import datetime, date, timedelta
import calendar

time_stamp_now = datetime.now()
time_stamp_plus = time_stamp_now + timedelta(minutes = 30) 
time_on=time_stamp_now.strftime('%H:%M')
time_after=time_stamp_plus.strftime('%H:%M')
my_date = date.today()
day=calendar.day_name[my_date.weekday()].lower()

time_on="08:00"
time_after="08:30"

url='https://api.transport.nsw.gov.au/v1/gtfs/schedule/buses/SMBSC008'
headers= {'Authorization' : 'apikey *****************', 'Accept' : 'application/octet-stream'}
routes=("2440_***", "2440_***", "2440_***")
e_routes=("2440_***", "2440_***")
home_stop="******"

def get_data():

   response = requests.get(url, headers=headers)

   with open('stream.zip', 'w') as outfile:
      outfile.write(response.content)


def update():
   cnx = mysql.connector.connect(user='root', database='buses', client_flags=[ClientFlag.LOCAL_FILES]) 
   cursor = cnx.cursor(buffered=True)
   zf = zipfile.ZipFile('stream.zip')
   for filename in ['calendar', 'stop_times','stops', 'trips']:
      del_query="""truncate {};""" 
      cursor.execute(del_query.format(filename))
      data = zf.extract(filename + '.txt', path='/tmp/')
      load_query="""LOAD DATA LOCAL INFILE '{}' 
      into TABLE {} 
      COLUMNS TERMINATED BY ',' 
      ENCLOSED BY '"' 
      LINES TERMINATED BY '\r\n' 
      IGNORE 1 LINES"""
      cursor.execute(load_query.format( data, filename))
      cnx.commit()
      cursor.close()
      cnx.close()

def next_buses():
   res = [] 
   cnx = mysql.connector.connect(user='root', database='buses', client_flags=[ClientFlag.LOCAL_FILES]) 
   cursor = cnx.cursor(buffered=True)
   query="""select distinct route_id, arrival_time
   from stop_times
   inner join trips on trips.trip_id = stop_times.trip_id
   where stop_times.trip_id in
   (select trip_id from trips inner join calendar
   on calendar.service_id = trips.service_id
   where route_id in {}
   and calendar.{}=1)
   and stop_id = "{}"
   and arrival_time > '{}'
   and arrival_time < '{}'
   order by arrival_time;"""
   cursor.execute(query.format(routes, day, home_stop, time_on, time_after))
   for col in cursor.fetchall():
        line = col[0][5:]
        arrival = col[1]
        trip = str(line) + " " +  str(arrival) + ","
        res.append(trip)
   cursor.close()
   cnx.close()
   return res


def next_e_buses():
   global routes
   routes = e_routes
   return next_buses()
