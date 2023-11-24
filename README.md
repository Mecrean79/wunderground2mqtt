# wunderground2mqtt

A docker image for Simple MQTT publisher of weather data using the WeatherUnderground API V2.
 -> Fork simonvanderveldt/mqtt-wunderground  (thanks to him)
 Connect to the "current condition" Domain (https://ibm.co/v2PWSCC) for 1 PWS only.
Publishes the temperature, relative humidity, precipitation, pressure, windspeed, winddirection and solar Radiation/uv from a given Personal Weather Station

## How it works
 - Create the http request for WUnderground API with os Environment config
 - Parse result of the request
 - Recreate json to publish on MQTT broker :
   -  New PWS Topic : <config 'MQTT_CONFIG_TOPIC'>/<config 'WU_STATIONID'>/station
     ex : station = {"obsTimeLocal":"2023-11-22 21:30:04","neighborhood":"Thouaré-sur-Loire","country":"FR"}
   - New Weather Topic : <config 'MQTT_CONFIG_TOPIC'>/<config 'WU_STATIONID'>/weatherInfo
     ex : weatherInfo = {"humidity":82.0,"uv":0,"winddir":'78.0,"solarRadiation":0}
   - Extract <unit> topic of WU API : <config 'MQTT_CONFIG_TOPIC'>/<config 'WU_STATIONID'>/<config 'WU_UNIT'>
     ex : uk_hybrid = {"temp":6.4,"heatIndex":6.4,"dewpt":5.3,"windChill":6.4,"windSpeed":0.0,"windGust":0.0,"pressure":1024.72,"precipRate":0.00,"precipTotal":0.00,"elev":24.0}


## Usage
### How to configure
wunderground2mqtt reads configuration from docker-compose.yml environment section.

Most of environment variables used :

	MQTT_HOST: MQTT broker ip adress (like 192.168.0.1) or localhost (localhost default)
	MQTT_PORT: Port number use by MQTT brocker (1883 if empty)
	MQTT_USERNAME: Username if credential activated on broker (if empty, anonymous connection)
	MQTT_PASSWORD: Password if credential activated on broker
	MQTT_PUBLISH_TOPIC: Root Topic use to add MQTT ibformation (default : wunderground)
	MQTT_CONFIG_TOPIC: Configuration topic to change configuration through MQQT (config/clients/wunderground by default)
	WU_API_KEY: Your WeatherUnderground API key (see https://www.wunderground.com/member/api-keys)
	WU_UPDATERATE: Integer - Time between request WU API in seconds (default 900)
	WU_STATIONID: Your WeatherUnderground PWS ID  (see https://www.wunderground.com/member/devices)
	WU_DECIMAL: Boolean - Add decimal to integer value return by WU API (default : True)
	WU_UNIT: version of unit json API (observations/0/<unit>). Values are m for metric (default), e for imperial and h for uk_hybrid
	  
### How to build/deploy
This repository/script designed for docker use.
Docker is required for use image/container.
If you want to use directly (without docker), you need to modify pyhton script (config values) [TODO : create standalone version]
With docker : 
1) Clone this repository to your local server
2) Build docker image Mecrean79/wunderground2mqtt in your local clone (ex cmd : docker build -t Mecrean79/wunderground2mqtt)
3) [TODO : push image on docker hub and add command]
4) Docker run or compose container (compose here) :
ex cmd in docker-compose.yml folder: docker compose up -d wunderground2mqtt
5) Check container execution or logs error

## TODO/improvments
- Multiples PWS
- Other WU API domains (7 days,...)
- Standalone version (no docker)
- Upload to docker hub
