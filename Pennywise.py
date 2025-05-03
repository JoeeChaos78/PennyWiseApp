
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Title and Header
st.set_page_config(page_title="PennyWise", layout="centered")
st.title("💰 PennyWise: Where your money meets mastery.")
st.markdown("**Simple. Smart. Saving.**")

# Load Google Service Account Credentials from Streamlit Secrets
service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/drive.file"]
)
FOLDER_ID = st.secrets["FOLDER_ID"]

# Google Drive Setup
drive_service = build("drive", "v3", credentials=credentials)

def upload_to_drive(local_file_path, filename_on_drive):
    file_metadata = {
        "name": filename_on_drive,
        "parents": [FOLDER_ID]
    }
    media = MediaFileUpload(local_file_path, resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return file.get("id")

# Tabs
tab1, tab2, tab3 = st.tabs(["📅 Daily Entries", "📊 Dashboard", "☁️ Cloud Sync"])

# Initialize session state
if "data" not in st.session_state:
    st.session_state["data"] = []

# Tab 1: Daily Entries
with tab1:
    st.subheader("📅 Daily Budget Entries")
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date")
        btype = st.selectbox("Type", ["Income", "Expense"])
    with col2:
        category = st.text_input("Category")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    notes = st.text_area("Notes", height=100)
    if st.button("➕ Add Entry"):
        entry = {
            "Date": str(date),
            "Type": btype,
            "Category": category,
            "Amount": amount,
            "Notes": notes
        }
        st.session_state.data.append(entry)
        st.success("Entry added!")

    # Display entries
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        st.dataframe(df, use_container_width=True)

# Tab 2: Dashboard
with tab2:
    st.subheader("📊 Budget Dashboard")
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        df["Amount"] = pd.to_numeric(df["Amount"])
        income = df[df["Type"] == "Income"]["Amount"].sum()
        expense = df[df["Type"] == "Expense"]["Amount"].sum()
        balance = income - expense

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"${income:,.2f}")
        col2.metric("Total Expense", f"${expense:,.2f}")
        col3.metric("Current Balance", f"${balance:,.2f}")

        # Bar chart by category
        fig = px.bar(df, x="Category", y="Amount", color="Type", barmode="group", title="Budget Summary by Category")
        st.plotly_chart(fig, use_container_width=True)

# Tab 3: Cloud Sync
with tab3:
    st.subheader("☁️ Save Data to Google Drive")
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        csv_path = "budget_data.csv"
        df.to_csv(csv_path, index=False)
        if st.button("⬆️ Upload to Drive"):
            file_id = upload_to_drive(csv_path, "budget_data.csv")
            st.success(f"Uploaded to Google Drive with File ID: {file_id}")
        os.remove(csv_path)
    else:
        st.info("No data to sync yet.")
