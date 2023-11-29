
import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go

# Initialize firebase app with credentials
if not firebase_admin._apps:
    # use streamlit secrets to get the firebase credentials
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"],
    })
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["databaseURL"]
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
# st.write("Latest temperature: ", latest['temperature'])
# st.write("Latest humidity: ", latest['humidity'])
# st.write("Latest pressure: ", latest['pressure'])
# st.write("Latest time: ", latest['date'])


st.title('Fridge Monitor')
st.header('Current Temperature')
# st.subheader('Current temperature is ' + str(latest['temperature']) + ' C')

fig_current = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = latest['temperature'],
    domain = {'x': [0, 1], 'y': [0, 1]},
    gauge = {'axis': {'range': [0, 10]},
             'bar': {'thickness': 0},
             'steps' : [
                 {'range': [0, 2], 'color': "orange"},
                 {'range': [2, 8], 'color': "lightblue"},
                 {'range': [8, 10], 'color': "orange"}],
             'threshold' : {'line': {'color': "black", 'width': 5}, 'thickness': 0.75, 'value': latest['temperature']}}))

fig_current.update_layout(autosize=True,title='Current Temperature', font_size=16)

st.plotly_chart(fig_current, use_container_width=True)

# get the last 30 days of temperature data using the date "date": "2023-11-08 14:27:01"
all_records = ref.order_by_key().get()
# make a dataframe from the data with date and temperature columns
df = pd.DataFrame.from_records(all_records)
df = df.transpose()
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
# limit the dataframe to the last 30 days
# Get the selected timeframe
timeframe = st.date_input('Select timeframe', [datetime.date.today() - datetime.timedelta(days=7), datetime.date.today()])

# Check if two dates are selected
if len(timeframe) == 2:
    start_date, end_date = timeframe
else:
    # If not, set default values
    start_date = datetime.date.today() - datetime.timedelta(days=7)
    end_date = datetime.date.today()
df = df[(df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))]

# Resample the DataFrame to a daily frequency and calculate the mean temperature for each day
df_daily = df.resample('D').mean()

fig = px.line(df, x=df.index, y='temperature', labels={'x':'Date', 'y':'Temperature (C)', 'title':'Temperature History'})

fig.update_layout(autosize=True,title='Temperature History', xaxis_title='Date', yaxis_title='Temperature (C)')

st.header('Temperature History')

st.plotly_chart(fig, use_container_width=True)

fig_curved = go.Figure()

fig_curved.add_trace(go.Scatter(x=df_daily.index, y=df_daily['temperature'], mode='lines', line_shape='spline', name='temperature'))

fig_curved.update_layout(autosize=True,title='Average Daily Temperature History', xaxis_title='Date', yaxis_title='Temperature (C)')

st.plotly_chart(fig_curved, use_container_width=True)