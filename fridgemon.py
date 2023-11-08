import smtplib
import ssl
import subprocess
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
# for dealing with attachement MIME types
from email.mime.text import MIMEText

# firebase imports
# --------- Firebase Settings ---------

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("/usr/local/bin/fridgemon/fridgemon-355420-firebase-adminsdk-xnf5p-3bff4c7a21.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fridgemon-355420-default-rtdb.firebaseio.com/'
})
ref = db.reference('/')

# ---------------------------------

import bme280
import mysql.connector
import smbus2

#Email Variables
# --------- Email Settings ---------
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
GMAIL_USERNAME = 'fridgealert7@gmail.com'
GMAIL_PASSWORD = 'jiutxeeyeidktczx'
EMAIL_TEMPLATE = '/usr/local/bin/fridgemon/index.html'
# ---------------------------------


# --------- User Settings ---------
SENSOR_LOCATION_NAME = "Dispensary fridge"
MINUTES_BETWEEN_READS = 10
MINUTES_BETWEEN_ALERTS = 60
threshold_upper = 9
threshold_lower = 2
sendTo = ['rohanday4@gmail.com', 'effinghampharmacy@telkomsa.net', 'krsna945@gmail.com']
# ---------------------------------

# Get email body html content from a file
def get_html_content(filename):
    with open(filename) as f:
        return f.read()

class Emailer:
    def __init__(self) -> None:
         self.context = ssl.create_default_context()

    def sendmail(self, recipients, subject, content) -> None:

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = GMAIL_USERNAME
        msg['To'] = ','.join(recipients)

        html = MIMEText(content, 'html')
        msg.attach(html)

        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls(context=self.context)

        #Send Email & Exit
        session.login(GMAIL_USERNAME, GMAIL_PASSWORD)
        session.sendmail(GMAIL_USERNAME, recipients, msg.as_string())
        session.quit()

class FridgeMonitor:
    def __init__(self, DEBUG=False) -> None:
        self.emailer = Emailer()
        self.sensor_location_name = SENSOR_LOCATION_NAME
        self.minutes_between_reads = MINUTES_BETWEEN_READS
        self.minutes_between_alerts = MINUTES_BETWEEN_ALERTS
        self.threshold_upper = threshold_upper
        self.threshold_lower = threshold_lower
        self.sensor_port = 1
        self.sensor_address = 0x77
        self.sensor_bus = smbus2.SMBus(self.sensor_port)
        self.sensor_calibration_params = bme280.load_calibration_params(self.sensor_bus, self.sensor_address)
        self.sensor = bme280.sample(self.sensor_bus, self.sensor_address, self.sensor_calibration_params)
        self.mydb = mysql.connector.connect(
            host="localhost",
            user="pharmacy",
            password="Crazyman@9",
            database="fridgedb"
        )
        self.mycursor = self.mydb.cursor()
        self.last_alert = datetime(1999, 1, 1)
        self.DEBUG = DEBUG
        self.temperature = 0
        self.humidity = 0
        self.pressure = 0
        self.timestamp = 0
        self.alertN = 0
        self.sensor_fetch()
        self.startup()

    def startup(self):
        html_content = get_html_content(EMAIL_TEMPLATE)
        ip = subprocess.check_output(['hostname', '-I'])
        # convert byte string to string
        ip = ip.decode('utf-8')
        html_content = html_content.replace("{alertTitle}", "I'm Alive!")
        html_content = html_content.replace("{alertSubtitle}", "Local IP: " + ip)
        html_content = html_content.replace("{timestamp}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        html_content = html_content.replace("{alertNumber}", "0")
        self.emailer.sendmail(sendTo, "Fridge Alert!", html_content)

    def sensor_fetch(self) -> None:
        self.sensor = bme280.sample(self.sensor_bus, self.sensor_address, self.sensor_calibration_params)
        self.temperature = round(self.sensor.temperature,1)
        self.humidity = self.sensor.humidity
        self.pressure = self.sensor.pressure
        self.timestamp = self.sensor.timestamp

    def sql_log(self, temperature, humidity, pressure):
        mydate = datetime.utcnow()
        mydatetime = mydate.strftime("%Y-%m-%d %H:%M:%S")
        sql = "INSERT INTO fridge_stats (Date, Temperature, Humidity, Pressure) VALUES (%s, %s, %s, %s)"
        val = (mydatetime, temperature, humidity, pressure)
        self.mycursor.execute(sql, val)
        self.mydb.commit()

    def firebase_log(self, temperature, humidity, pressure):
        mydate = datetime.utcnow()
        mydatetime = mydate.strftime("%Y-%m-%d %H:%M:%S")
        sensor_ref = ref.child('sensor')
        sensor_ref.push({
            'date': mydatetime,
            'temperature': temperature,
            'humidity': humidity,
            'pressure': pressure
        })

    def send_alert(self, temperature, alert_type):
        # dictionary of strings for different alert titles
        alert_title = {
            "high": "Temperature too high",
            "low": "Temperature too low",
            "normal": "Temperature normalized"
        }
        # dictionary of strings for different alert subtitles
        alert_subtitle = {
            "high": "Temperature: " + str(temperature) + "\u00b0C",
            "low": "Temperature: " + str(temperature) + "\u00b0C",
            "normal": "All good! Temperature: " + str(temperature) + "\u00b0C"
        }

        # get html content
        html_content = get_html_content(EMAIL_TEMPLATE)
        html_content = html_content.replace("{alertTitle}", alert_title[alert_type])
        html_content = html_content.replace("{alertSubtitle}", alert_subtitle[alert_type])
        html_content = html_content.replace("{timestamp}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        html_content = html_content.replace("{alertNumber}", str(self.alertN))
        self.emailer.sendmail(sendTo, "Fridge Alert!", html_content)

    def run(self):
        while True:
            self.sensor_fetch()
            self.sql_log(self.temperature, self.humidity, self.pressure)
            self.firebase_log(self.temperature, self.humidity, self.pressure)
            if self.temperature >= self.threshold_lower and self.temperature <= self.threshold_upper:
                if self.DEBUG:
                    print("Temperature is normal")
                if self.last_alert < datetime.now() - timedelta(minutes=self.minutes_between_alerts) and self.alertN > 0:
                    self.send_alert(self.temperature, "normal")
                    self.last_alert = datetime.now()
                    self.alertN = 0
            elif self.temperature > self.threshold_upper:
                if self.DEBUG:
                    print("Temperature is too high")
                if self.last_alert < datetime.now() - timedelta(minutes=self.minutes_between_alerts):
                    self.send_alert(self.temperature, "high")
                    self.last_alert = datetime.now()
                    self.alertN += 1
            elif self.temperature < self.threshold_lower:
                if self.DEBUG:
                    print("Temperature is too low")
                if self.last_alert < datetime.now() - timedelta(minutes=self.minutes_between_alerts):
                    self.send_alert(self.temperature, "low")
                    self.last_alert = datetime.now()
                    self.alertN += 1
            if self.DEBUG:
                print("-------------------- Reading --------------------")
                print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                print("Temperature: " + str(self.temperature) + "\u00b0C")
                print("Humidity: " + str(self.humidity) + "%")
                print("Pressure: " + str(self.pressure) + "hPa")
                print("Sensor Timestamp: " + str(self.timestamp))
                print("Last Alert: " + str(self.last_alert))
                print("Alert Number: " + str(self.alertN))
                print("------------------------------------------------")
                print("")

            time.sleep(self.minutes_between_reads * 60)

# Define a callback function to handle changes to the refresh_request node
def handle_refresh_request(event):
    fridge_monitor.firebase_log(fridge_monitor.temperature, fridge_monitor.humidity, fridge_monitor.pressure)


if __name__ == "__main__":
    # Listen for changes in the refresh_request node
    fridge_monitor = FridgeMonitor()
    refresh_ref = ref.child('refresh_request')
    refresh_ref.listen(handle_refresh_request)
    fridge_monitor.run()