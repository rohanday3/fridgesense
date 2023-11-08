
import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pandas as pd

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

# get the last 30 days of temperature data using the date
last30 = ref.order_by_child('date').limit_to_last(30).get()
# make a dataframe from the data with date and temperature columns
df = pd.DataFrame(last30)
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
st.line_chart(df['temperature'], key='temp', use_container_width=True, height=300, width=300, title='Temperature', x_axis='Date', y_axis='Temperature (C)', help='Temperature over the last month')

# Resample the DataFrame to a daily frequency and calculate the mean temperature for each day
df_daily = df.resample('D').mean()

# Pass this resampled DataFrame to the st.line_chart function
st.line_chart(df_daily['temperature'], key='temp', use_container_width=True, height=300, width=300, title='Average Daily Temperature', x_axis='Date', y_axis='Temperature (C)', help='Average temperature per day over the last month')