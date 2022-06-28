#!/bin/bash

### BEGIN INIT INFO
# Provides:          recognition
# Required-Start:    $syslog $network
# Required-Stop:     $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts the recognition
# Description:       starts recognition using start-stop-daemon
### END INIT INFO

opencv_service_start() {
    echo -n "Starting python: "
    echo "---------------------------------------------------------------------------------" >>/var/log/recognition
    date +"! %Y/%m/%d %a %T : Starting python ." >>/var/log/recognition
    echo start
    source /home/pi/Desktop/opencv-env/bin/activate
    cd /home/pi/Desktop/python_05_12
    python3 -u mqtt_for_image.py > /home/pi/Desktop/python_05_12/execution_output.log 2>&1 &
    echo "Done."
    echo ""
    date +"! %Y/%m/%d %a %T : Finished." >>/var/log/recognition
    echo "---------------------------------------------------------------------------------" >>/var/log/recognition
    touch /var/lock/subsys/python
}

opencv_service_stop() {
    echo -n "Shutting Down python Listeners: "
    echo "---------------------------------------------------------------------------------" >>/var/log/recognition
    date +"! %Y/%m/%d %a %T : Shutting Down python." >>/var/log/recognition
    echo "python"
    killall -9 python3
    echo "Done."
    rm -f /var/lock/subsys/python
    echo "Done."
    date +"! %Y/%m/%d %a %T : Finished." >>/var/log/recognition
    echo "---------------------------------------------------------------------------------" >>/var/log/recognition
}

opencv_service_restart() {
    opencv_service_stop
    opencv_service_start
}

case "$1" in
    start)
        opencv_service_start
        ;;
    stop)
        opencv_service_stop
        ;;
    restart)
        opencv_service_restart
        ;;
    *)
        echo "Usage: recognition { start | stop | restart }"
        exit 1
        ;;
esac
exit 0
