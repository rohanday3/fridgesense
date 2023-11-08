
import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Initialize firebase app with credentials
cred = credentials.Certificate("fridgemon-355420-b1b55a0a251b.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fridgemon-355420-default-rtdb.firebaseio.com/'
})

# Get reference to the temperature data in firebase
ref = db.reference('sensor')

# {
#   "-NijK4ZOPUFZvCMsCgY7": {
#     "date": "2023-11-08 14:27:01",
#     "humidity": 42.71894478830491,
#     "pressure": 1006.0541413630464,
#     "temperature": 6.8
#   }
# }

# display the latest temperature, humidity, and pressure and the time it was recorded
latest = ref.order_by_key().limit_to_last(1).get()
latest = list(latest.values())[0]
st.write("Latest temperature: ", latest['temperature'])
st.write("Latest humidity: ", latest['humidity'])
st.write("Latest pressure: ", latest['pressure'])
st.write("Latest time: ", latest['date'])

# display the average temperature, humidity, and pressure over the last 24 hours
last24 = ref.order_by_key().limit_to_last(24).get()
last24 = list(last24.values())
avg_temp = sum([x['temperature'] for x in last24]) / len(last24)
avg_hum = sum([x['humidity'] for x in last24]) / len(last24)
avg_pres = sum([x['pressure'] for x in last24]) / len(last24)
st.write("Average temperature: ", avg_temp)
st.write("Average humidity: ", avg_hum)
st.write("Average pressure: ", avg_pres)

# display the average temperature, humidity, and pressure over the last 7 days
last7 = ref.order_by_key().limit_to_last(168).get()
last7 = list(last7.values())

avg_temp = sum([x['temperature'] for x in last7]) / len(last7)
avg_hum = sum([x['humidity'] for x in last7]) / len(last7)
avg_pres = sum([x['pressure'] for x in last7]) / len(last7)
st.write("Average temperature: ", avg_temp)
st.write("Average humidity: ", avg_hum)
st.write("Average pressure: ", avg_pres)

# display a line chart of the temperature over the last month
last30 = ref.order_by_key().limit_to_last(720).get()
last30 = list(last30.values())
last30 = sorted(last30, key=lambda x: x['date'])
st.line_chart([x['temperature'] for x in last30])

# display a line chart of the average temperature, humidity, and pressure per day over the last month
last30 = ref.order_by_key().limit_to_last(720).get()
last30 = list(last30.values())
# remove the time from the date and get the average for each day
for x in last30:
    x['date'] = x['date'].split(' ')[0]
last30 = sorted(last30, key=lambda x: x['date'])
st.line_chart([x['temperature'] for x in last30])
st.line_chart([x['humidity'] for x in last30])
st.line_chart([x['pressure'] for x in last30])