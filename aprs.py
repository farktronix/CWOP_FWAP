#!/usr/local/bin/python3

import aprslib
import conf
import time
from influxdb import InfluxDBClient
import logging
logging.basicConfig(level=logging.DEBUG)

# Function taken from 
"""
initially from Tom Hayward
builds and submits
APRS weather packet to the APRS-IS/CWOP.
BSD License and stuff
Copyright 2010 Tom Hayward <tom@tomh.us>

# SwitchDoc Labs
# July 24, 2015
# Version 1.0

"""
def make_aprs_wx(wind_dir=None, wind_speed=None, wind_gust=None, temperature=None, humidity=None, pressure=None, luminosity=None):
    """
    Assembles the payload of the APRS weather packet.
    """
    def str_or_dots(number, length):
        """
        If parameter is None, fill space with dots. Else, zero-pad.
        """
        if number is None:
            return '.'*length
        else:
            format_type = {
                'int': 'd',
                'float': '.0f',
            }[type(number).__name__]
            return ''.join(('%0',str(length),format_type)) % number
    timeStringZulu = time.strftime("%d%H%M")
    formatString = '@%sz%s/%s_%s/%sg%st%sh%sb%sL%s%s'
    if luminosity is not None and luminosity >= 1000:
        formatString = '@%sz%s/%s_%s/%sg%st%sh%sb%sl%s%s'
        luminosity -= 1000
    return formatString % (
        timeStringZulu,
        conf.latitude,
        conf.longitude,
        str_or_dots(wind_dir, 3),
        str_or_dots(wind_speed, 3),
        str_or_dots(wind_gust, 3),
        str_or_dots(temperature, 3),
        str_or_dots(humidity, 2),
        str_or_dots(pressure, 5),
        str_or_dots(luminosity, 3),
        conf.stationVersion
    )


def sendAPRSPacket(packet):
    print("Packet is " + packet)
    aprs = aprslib.IS(conf.callsign, passwd=conf.password, host=conf.server, port=conf.port)
    aprs.connect()
    aprs.sendall(packet)

def getSensorValueFromInflux(client, fieldname):
    val = None
    results = client.query('SELECT mean(' + fieldname + ') FROM "' + conf.influx_fromField +'" WHERE ("host" = \'FWAPOutside\') AND time > now() - 10m GROUP BY time(10m) fill(null)', bind_params={"sensorHost" : conf.influx_sensorHost})
    print(results)
    for item in results.items():
        result = next(item[1])
        val = result['mean']
    return val

def getInfluxWeatherData():
    client = InfluxDBClient(host=conf.influx_host)
    client.switch_database(conf.influx_db)

    temp = getSensorValueFromInflux(client, "temperature") * 1.8 + 32.00
    humidity = getSensorValueFromInflux(client, "humidity")
    pressure = getSensorValueFromInflux(client, "pressure")

    return make_aprs_wx(temperature=temp, humidity=humidity, pressure=pressure)

header = '%s>APRS,TCPIP*:' % conf.callsign
weatherData = getInfluxWeatherData()
packet = header + weatherData
sendAPRSPacket(packet)

