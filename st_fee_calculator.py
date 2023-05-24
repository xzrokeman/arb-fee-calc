import streamlit as st
from fee_calculator import *

AID = st.number_input('AID', min=0)

domestic = st.write(sciaDomestic(AID))
