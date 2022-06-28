#!/bin/sh

set -e

if ( [ -z "${MOSQUITTO_USERNAME}" ] || [ -z "${MOSQUITTO_PASSWORD}" ] ); then
  echo "MOSQUITTO_USERNAME or MOSQUITTO_PASSWORD not defined"
  exit 1
fi

# create mosquitto passwordfile
cd /mosquitto
touch passwordfile
mosquitto_passwd -b passwordfile $MOSQUITTO_USERNAME $MOSQUITTO_PASSWORD

touch "$MOSQUITTO_LOGFILENAME"
chmod 007 "$MOSQUITTO_LOGFILENAME"
# touch /mosquitto/log/02_13_mosquitto.log
# # change log file permission
# chmod 007 /mosquitto/log/02_13_mosquitto.log


exec "$@"
