#!/usr/bin/python3
"""
wunderground2mqtt.py
A docker image for Simple MQTT publisher of weather data using the WeatherUnderground API V2.
Connect to the "current condition" Domain (https://ibm.co/v2PWSCC) for 1 PWS only.
Publishes the temperature, relative humidity, precipitation, pressure,
windspeed, winddirection and solar Radiation/uv from a given Personal Weather Station
"""

# IMPORTS
import urllib.request
import urllib.error
import json
import paho.mqtt.client as paho
import time
import os
import logging

# Log to STDOUT
logger = logging.getLogger("mqtt-wunderground")
logger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)

# Component config
config = {}

# Get MQTT servername/address
# Supports Docker environment variable format MQTT_HOST = #.#.#.# and MQTT_PORT
config['mqtt_brocker'] = os.environ.get('MQTT_HOST')
config['mqtt_port'] = os.environ.get('MQTT_PORT')
if config['mqtt_brocker'] is None:
    logger.info("MQTT_HOST is not set, using default localhost")
    config['mqtt_brocker'] = "localhost"
if config['mqtt_port'] is None:
    logger.info("MQTT_PORT is not set, using default 1883")
    config['mqtt_port'] = 1883

# Get MQTT username/password
# Supports Docker environment variable format MQTT_USERNAME and MQTT_PASSWORD
config['mqtt_username'] = os.environ.get('MQTT_USERNAME')
if config['mqtt_username'] is None:
    logger.info("MQTT_USERNAME is not set, anonymous MQTT connection")
else:
    logger.info("MQTT_USERNAME is set, MQTT connection with credential")
    config['mqtt_password'] = os.environ.get('MQTT_PASSWORD')

# Get config topic
# Supports Docker environment variable format MQTT_CONFIG_TOPIC
config['config_topic'] = os.environ.get('MQTT_CONFIG_TOPIC')
if config['config_topic'] is None:
    logger.info("MQTT_CONFIG_TOPIC is not set, exiting")
    raise SystemExit

# Get Weather Underground API key
# Supports Docker environment variable format WU_API_KEY
config['wu_api_key'] = os.environ.get('WU_API_KEY')
if config['wu_api_key'] is None:
    logger.info("WU_API_KEY is not set, exiting")
    raise SystemExit

# Get MQTT Topic to use
# Supports Docker environment variable format MQTT_PUBLISH_TOPIC
config['publish_topic'] = os.environ.get('MQTT_PUBLISH_TOPIC')
if config['publish_topic'] is None:
    logger.info("MQTT_PUBLISH_TOPIC is not set, exiting")
    raise SystemExit

# Get Update rate to get WU informations
# Supports Docker environment variable format WU_UPDATERATE
config['updaterate'] = os.environ.get('WU_UPDATERATE')
if config['updaterate'] is None:
    logger.info("WU_UPDATERATE is not set, use root 900 seconds")
    config['updaterate'] = 900

# Get stationid for Weather Underground
# Supports Docker environment variable format WU_STATIONID
config['stationid'] = os.environ.get('WU_STATIONID')
if config['stationid'] is None:
    logger.info("stationid is not set, exiting")
    raise SystemExit

# Get Numeric Precision
# Supports Docker environment variable format WU_DECIMAL
booldecimal = os.getenv("WU_DECIMAL", 'False').lower() in ('true', '1', 't')
if booldecimal is None or booldecimal != True:
    logger.info("WU_DECIMAL is not set, incorrect or false, use no decimal")
    config['numericprecision'] = ""
else:
    config['numericprecision'] = "&numericPrecision=decimal"

# Get unit for Weather Underground
# Supports Docker environment variable format WU_UNIT
config['unit'] = os.environ.get('WU_UNIT')
if config['unit'] is None or (config['unit'] != "m" and config['unit'] != "e" and config['unit'] != "h"):
    logger.info("WU_UNIT is not set or incorrect, use metric")
    config['unit'] = "m"
# Add description unit for mqtt
match config['unit']:
   case "m":
    unitDesc = "metric"
   case "e":
    unitDesc = "imperial"
   case "h":
    unitDesc = "uk_hybrid"

# Create the callbacks for Mosquitto
def on_connect(self, mosq, obj, rc):
    if rc == 0:
        logger.info("Connected to broker " + str(config['mqtt_brocker'] + ":" + str(config['mqtt_port'])))
        # Subscribe to device config
        logger.info("Subscribing to device config at " + config['config_topic'] + "/#")
        mqttclient.subscribe(config['config_topic'] + "/#")


def on_subscribe(mosq, obj, mid, granted_qos):
    logger.info("Subscribed with message ID " + str(mid) + " and QOS " + str(granted_qos) + " acknowledged by broker")


def on_message(mosq, obj, msg):
    logger.info("Received message: " + msg.topic + ":" + msg.payload)
    if msg.topic.startswith(config['config_topic']):
        configitem = msg.topic.split('/')[-1]
        if configitem in config:
            # TODO unset when value set to ""
            logger.info("Setting configuration " + configitem + " to " + msg.payload)
            config[configitem] = msg.payload
        else:
            logger.info("Ignoring unknown configuration item " + configitem)


def on_publish(mosq, obj, mid):
    # logger.info("Published message with message ID: "+str(mid))
    pass


def wunderground_get_weather():
    # Parse the WeatherUnderground json response
    wu_url = "https://api.weather.com/v2/pws/observations/current?stationId=" + config['stationid'] + "&format=json&units=" + config['unit'] + "&apiKey=" + config['wu_api_key'] + config['numericprecision']
    logger.info("Getting Weather Underground data from " + wu_url)

    try: 
        resonse = urllib.request.urlopen(wu_url)
    except urllib.error.URLErrorr as e:
        logger.error('URLError: ' + str(wu_url) + ': ' + str(e.reason))
        return None
    except Exception:
        import traceback
        logger.error('Exception: ' + traceback.format_exc())
        return None

    parsed_json = json.load(resonse)
    resonse.close()

    station_json_str = '{"obsTimeLocal":"'+ str(parsed_json['observations'][0]['obsTimeLocal'])+'","neighborhood":"'+ str(parsed_json['observations'][0]['neighborhood'])+'","country":"'+ str(parsed_json['observations'][0]['country'])+'"}'
    weather_json_str = '{"humidity":'+ str(parsed_json['observations'][0]['humidity'])+',"uv":'+ str(parsed_json['observations'][0]['uv'])+',"winddir":'+ str(parsed_json['observations'][0]['winddir'])+',"solarRadiation":'+ str(parsed_json['observations'][0]['solarRadiation'])+'}'
    metric_json_str = str(parsed_json['observations'][0][unitDesc]).replace("'", '"')

#   Publish the values we parsed from the feed to the broker
    mqttclient.publish(config['publish_topic'] + "/"+config['stationid']+"/station", station_json_str, retain=True)
    mqttclient.publish(config['publish_topic'] + "/"+config['stationid']+"/weatherInfo", weather_json_str, retain=True)
    mqttclient.publish(config['publish_topic'] + "/"+config['stationid']+"/"+unitDesc, metric_json_str, retain=True)

    logger.info("Published " + str(config['stationid']) + " data to " + str(config['publish_topic']))


# Create the Mosquitto client
mqttclient = paho.Client()

# Bind the Mosquitte events to our event handlers
mqttclient.on_connect = on_connect
mqttclient.on_subscribe = on_subscribe
mqttclient.on_message = on_message
mqttclient.on_publish = on_publish


# Connect to the Mosquitto broker
logger.info("Connecting to broker " + config['mqtt_brocker'] + ":" + str(config['mqtt_port']))
if config['mqtt_username'] is not None:
    mqttclient.username_pw_set(config['mqtt_username'], config['mqtt_password'])
mqttclient.connect(config['mqtt_brocker'], config['mqtt_port'], 60)

# Start the Mosquitto loop in a non-blocking way (uses threading)
mqttclient.loop_start()

time.sleep(5)

rc = 0
while rc == 0:
    wunderground_get_weather()
    time.sleep(float(config['updaterate']))
    pass
