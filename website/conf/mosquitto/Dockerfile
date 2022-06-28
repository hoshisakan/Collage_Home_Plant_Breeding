FROM eclipse-mosquitto:latest

COPY docker-entrypoint.sh /

EXPOSE 1883 8883

ENTRYPOINT ["sh", "./docker-entrypoint.sh"]

CMD ["/usr/sbin/mosquitto", "-c", "/mosquitto/config/mosquitto.conf"]
