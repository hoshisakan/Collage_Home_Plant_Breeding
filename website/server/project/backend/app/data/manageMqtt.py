from mainMqtt import create_mqtt_app
from flask import current_app

mqtt_app = create_mqtt_app()

# TODO 如果此程式是直接被執行，而非被當成一個模組執行，則會執行第6行的程式
if __name__ == '__main__':
  mqtt_app.run(debug=current_app.config['DEBUG'],
          use_reloader=current_app.config['DEBUG'],
          host='0.0.0.0')
