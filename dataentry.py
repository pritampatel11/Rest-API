import streamlit as st
import pandas as pd
from openpyxl import Workbook
import os
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from datetime import datetime

# Directory to save uploaded files
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Function to load existing data from the Excel file or create a new one if it doesn't exist
def load_data(file_path):
    if os.path.exists(file_path):
        data = pd.read_excel(file_path, engine='openpyxl', dtype=str)
    else:
        data = pd.DataFrame(columns=[
            "Issue Logged Date", "Ship Name", "Condition", "Ship Class", "Voyage Priority", 
            "Apprx Variance against Veson Desc(%)", "Dry Dock Date", "Propeller Polishing Date", 
            "Under Water Cleaning Date", "EOPD Updates", "Remarks", "Attachments"
        ])
        data.to_excel(file_path, index=False, engine='openpyxl')
    return data

# Function to append new data to the Excel file
def append_data(file_path, new_data):
    if os.path.exists(file_path):
        existing_data = pd.read_excel(file_path, engine='openpyxl', dtype=str)
        data = pd.concat([existing_data, new_data], ignore_index=True)
    else:
        data = new_data
    data.to_excel(file_path, index=False, engine='openpyxl')

# Function to save the entire data to the Excel file
def save_data(file_path, data):
    data.to_excel(file_path, index=False, engine='openpyxl')

# Function to save uploaded files and return their paths
def save_uploaded_files(uploaded_files, ship_name, issue_logged_date):
    saved_files = []
    subfolder = os.path.join(UPLOAD_DIR, f"{ship_name}_{issue_logged_date}")
    if not os.path.exists(subfolder):
        os.makedirs(subfolder)
    for uploaded_file in uploaded_files:
        file_path = os.path.join(subfolder, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_files.append(file_path)
    return saved_files

# Function to convert DataFrame to Excel bytes
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    processed_data = output.getvalue()
    return processed_data

# Load existing data
file_path = "test.xlsx"
data = load_data(file_path)

# Streamlit UI
st.set_page_config(page_title="🛠️Technical Issue Logger", page_icon="📝", layout="wide")
st.title("Technical Issue Logger")

# Sidebar for filters and download button
st.sidebar.header("Filters")

ship_name_filter = st.sidebar.multiselect(
    "Select Ship Name",
    options=data["Ship Name"].unique(),
    default=[]
)

voyage_priority_filter = st.sidebar.multiselect(
    "Select Voyage Priority",
    options=["Min Voyage Cost", "Min Bunker Cons", "Warranty", "Reporting"],
    default=[]
)

condition_filter = st.sidebar.multiselect(
    "Select Condition",
    options=["Laden", "Ballast"],
    default=[]
)

# Apply filters to the data
filtered_data = data.copy()
if ship_name_filter:
    filtered_data = filtered_data[filtered_data["Ship Name"].isin(ship_name_filter)]

if voyage_priority_filter:
    filtered_data = filtered_data[filtered_data["Voyage Priority"].isin(voyage_priority_filter)]

if condition_filter:
    filtered_data = filtered_data[filtered_data["Condition"].isin(condition_filter)]

# Add download button in the sidebar
st.sidebar.markdown("### Download Data")
excel_data = to_excel(filtered_data)
st.sidebar.download_button(
    label="⬇️Download",
    data=excel_data,
    file_name='technical_issue_log.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

# Data entry form
col1, col2, col3 = st.columns(3)

with col1:
    issue_logged_date = st.date_input("Issue Logged Date")
    ship_name = st.text_input("Ship Name")
    condition = st.selectbox("Condition", ["Laden", "Ballast"])

with col2:
    ship_class = st.selectbox("Ship Class", ["Capes", "Baby Capes", "Panamax", "Handy-Supra"])
    voyage_priority = st.selectbox("Voyage Priority", ["Min Voyage Cost", "Min Bunker Cons", "Warranty", "Reporting"])
    variance = st.number_input("Apprx Variance against Veson Desc(%)", min_value=0.0, max_value=100.0, format="%.2f")

with col3:
    dry_dock_date = st.date_input("Dry Dock Date")
    propeller_polishing_date = st.date_input("Propeller Polishing Date")
    under_water_cleaning_date = st.date_input("Under Water Cleaning Date")

col4, col5 = st.columns(2)
with col4:
    eopd_updates = st.text_area("EOPD Updates")
with col5:
    remarks = st.text_area("Remarks")

uploaded_files = st.file_uploader("Attach files", type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx"], accept_multiple_files=True)

if st.button("Submit"):
    issue_logged_date_str = issue_logged_date.strftime("%Y-%m-%d")
    saved_files = save_uploaded_files(uploaded_files, ship_name, issue_logged_date_str)
    new_data = pd.DataFrame({
        "Issue Logged Date": [issue_logged_date],
        "Ship Name": [ship_name],
        "Condition": [condition],
        "Ship Class": [ship_class],
        "Voyage Priority": [voyage_priority],
        "Apprx Variance against Veson Desc(%)": [variance],
        "Dry Dock Date": [dry_dock_date],
        "Propeller Polishing Date": [propeller_polishing_date],
        "Under Water Cleaning Date": [under_water_cleaning_date],
        "EOPD Updates": [eopd_updates],
        "Remarks": [remarks],
        "Attachments": [", ".join(saved_files)]
    }, dtype=str)
    append_data(file_path, new_data)
    st.success("Entry added successfully!")
    data = load_data(file_path)
    if ship_name_filter:
        data = data[data["Ship Name"].isin(ship_name_filter)]
    if voyage_priority_filter:
        data = data[data["Voyage Priority"].isin(voyage_priority_filter)]
    if condition_filter:
        data = data[data["Condition"].isin(condition_filter)]

# Add Serial Number column if it doesn't exist
if 'Sl No.' not in data.columns:
    data.reset_index(drop=True, inplace=True)
    data.index += 1
    data.index.name = "Sl No."
    data = data.reset_index()

# Use AgGrid to display the DataFrame with tooltips for the Notes column
st.write("Entries made:")

# Configure AgGrid options
gb = GridOptionsBuilder.from_dataframe(data)
gb.configure_column("Sl No.", pinned="left")
gb.configure_column("EOPD Updates", tooltipField="EOPD Updates")
gb.configure_column("Remarks", tooltipField="Remarks")
gb.configure_column("Attachments", tooltipField="Attachments")
grid_options = gb.build()

# Add custom CSS to ensure tooltips are styled correctly
st.markdown(
    """
    <style>
    .ag-theme-streamlit .ag-cell {
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Display the data table
AgGrid(
    data,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    theme='streamlit',
    height=400,
    reload_data=True
)
