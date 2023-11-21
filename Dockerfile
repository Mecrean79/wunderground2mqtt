FROM alpine:latest

RUN apk add python3 py3-pip && pip install paho-mqtt

ADD wunderground2mqtt.py /
CMD ["/wunderground2mqtt.py"]
