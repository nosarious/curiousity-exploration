#this file includes code from several sources.
import time
import datetime
import grovepi
import math
import serial
import re
from Adafruit_BME280 import *
import Adafruit_GPIO.I2C as I2C
en_debug = True

def debug(in_str):
	if en_debug:
		print(in_str)

#Getting the barometer sensor information - requires installing Adafruit GPIO library
sensor = BME280(t_mode=BME280_OSAMPLE_8, p_mode=BME280_OSAMPLE_8, h_mode=BME280_OSAMPLE_8)

#prep the serial for the gps 
ser = serial.Serial('/dev/ttyAMA0',  9600, timeout = 0.1)	#Open the serial port at 9600 baud
ser.flush()

#find the time to use for the file name
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')+".csv"

#Theoretically this is supposed to grab GPS coordinates. 
def readlineCR():
    rv = ""
    while True:
        time.sleep(0.001)	# This is the critical part.  A small pause 
        					# works really well here.
        ch = ser.read()        
        rv += ch
        if ch=='\r' or ch=='':
            return rv
 
class GPS:
	#The GPS module used is a Grove GPS module http://www.seeedstudio.com/depot/Grove-GPS-p-959.html
	inp=[]
	# Refer to SIM28 NMEA spec file http://www.seeedstudio.com/wiki/images/a/a0/SIM28_DATA_File.zip
	GGA=[]
 
	#Read data from the GPS
	def read(self):	
		while True:
			# GPS.inp=ser.readline()
			GPS.inp = readlineCR().strip()
			if GPS.inp[:6] =='$GPGGA': # GGA data , packet 1, has all the data we need
				break
			time.sleep(0.1)
		try:
			ind=GPS.inp.index('$GPGGA',5,len(GPS.inp))	#Sometimes multiple GPS data packets come into the stream. Take the data only after the last '$GPGGA' is seen
			GPS.inp=GPS.inp[ind:]
		except ValueError:
			print ("")
		GPS.GGA=GPS.inp.split(",")	#Split the stream into individual parts
		return [GPS.GGA]
 
	#Split the data into individual elements
	def vals(self):
		time=GPS.GGA[1]
		lat=GPS.GGA[2]
		lat_ns=GPS.GGA[3]
		long=GPS.GGA[4]
		long_ew=GPS.GGA[5]
		fix=GPS.GGA[6]
		sats=GPS.GGA[7]
		alt=GPS.GGA[9]
		return [time,fix,sats,alt,lat,lat_ns,long,long_ew]
 
g=GPS()



sensor0 = 0		 #sound sensor
sensor1 = 1		 
sensor2 = 2	     #light sensor

#temphum on D4
temp_hum_sensor = 4
#sensor type
blue = 0
white = 1


if __name__ == "__main__":
    f=open(st,'w')	#Open file to log the data
    f.write("light,sound,tempt,humidity,degrees,hectopascals,humidity,\n")	#Write the header to the top of the file

    while True:
        try:
            #get the barmeter information
            degrees = sensor.read_temperature()
            pascals = sensor.read_pressure()
            hectopascals = (pascals / 100)
            humidity = sensor.read_humidity()
            
            #print ('Temp      = {0:0.3f} deg C'.format(degrees))
            #print ('Pressure  = {0:0.2f} hPa'.format(hectopascals))
            #print ('Humidity  = {0:0.2f} %'.format(humidity))
            
            bar_string = str("%.2f" % degrees)+","+str("%.2f" % hectopascals)+","+str("%.2f" % humidity)

            #sensor 0 = sound. Sensor2 = light
            sensor_value0 = grovepi.analogRead(sensor0)
            sensor_value1 = grovepi.analogRead(sensor1)
            sensor_value2 = grovepi.analogRead(sensor2)
            
            #temperature sensor data
            temperatureV = 0
            humidityV = 0
            
            [temp,humidity] = grovepi.dht(temp_hum_sensor,blue)
            if math.isnan(temp) == False and math.isnan(humidity) == False:
                #print("temp = %.02f C humidity = %.02f%%" %(temp, humidity))
                temperatureV = temp
                humidityV = humidity
                
            #get the GPS data, or return 'bno data' if there is none
            try:
                x=g.read()	#Read from GPS
                [t,fix,sats,alt,lat,lat_ns,long,long_ew]=g.vals()	#Get the individial values
                print ("Time:",t,"Fix status:",fix,"Sats in view:",sats,"Altitude",alt,"Lat:",lat,lat_ns,"Long:",long,long_ew)
                gps_string=str(t)+","+str(float(lat)/100)+","+str(float(long)/100)+"\n"
            except:
                gps_string = " no data from GPS"
            
            #construct the string to save to file
            savetext=str(sensor_value0)+","+str(sensor_value2)+","+str(temperatureV)+","+str(humidityV)+","+bar_string+","+gps_string+"\n"
            debug(savetext)
        
            f.write(savetext)	#Save to file
            
            #slight pause, otherwise temp/hum returns no value
            time.sleep(1.5)
        
        except IOError:
            print("error")
        except KeyboardInterrupt:
            f.close()
            print ("Exiting")
	    
	    
