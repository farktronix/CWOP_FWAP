FROM python:3.6.12-alpine3.12
MAINTAINER farktronix

RUN pip3 install influxdb aprslib conf pyyaml

COPY crontab /etc/crontabs/root

COPY aprs.py /root/
RUN chmod +x /root/aprs.py

ENTRYPOINT ["crond", "-f", "-d", "8"]
#ENTRYPOINT ["/root/aprs.py", "--config", "/config.yml"]
