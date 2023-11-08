
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

# Query the latest temperature data
latest_temp = ref.order_by_key().limit_to_last(1).get()

# Display the latest temperature data in the streamlit app
st.write("Latest temperature:", latest_temp)

# display the historic temperature data for the last 3 months as a line chart
st.line_chart(ref.order_by_key().limit_to_last(90).get())