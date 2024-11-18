import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import io
import base64
import csv
import os
import json

# Constants
load_dotenv()
SERVICE_ACCOUNT_FILE = 'key.json'  # Replace with the path to your service account JSON file
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = os.getenv("FOLDER_ID")
CSV_FILE_NAME = os.getenv("SOURCE_FILE")
PAGE_SIZE = 20

encoded_creds = os.getenv('VIGILANTAI_SERVICE_ACCOUNT_KEY')
decoded_creds = base64.b64decode(encoded_creds)
service_account_info = json.loads(decoded_creds)

# Get Google Drive credentials
def get_credentials():
    # credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    scoped_credentials = credentials.with_scopes(SCOPES)
    return scoped_credentials

# Connect to Google Drive API and download the CSV file
def download_csv_from_gdrive():
    credentials = get_credentials()
    service = build('drive', 'v3', credentials=credentials)

    # Search for the CSV file in the folder
    query = f"'{FOLDER_ID}' in parents and name='{CSV_FILE_NAME}'"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])

    if not items:
        st.error('No CSV file found in the specified Google Drive folder.')
        return None

    file_id = items[0]['id']
    
    # Download the CSV file content
    request = service.files().get_media(fileId=file_id)
    file_content = io.BytesIO(request.execute())

    # Read CSV into a pandas DataFrame
    data = pd.read_csv(file_content)
    return data

# Function to display customers with pagination
def display_customers(st, current_page):
    st.title("Customers Table")

    # Download and display the CSV data
    data = download_csv_from_gdrive()
    
    if data is not None:
        total_pages = (len(data) + PAGE_SIZE - 1) // PAGE_SIZE  # Calculate total pages
        paginated_data = data.iloc[current_page * PAGE_SIZE:(current_page + 1) * PAGE_SIZE]  # Paginate data

        st.dataframe(paginated_data)

        # Display pagination buttons
        cols = st.columns(total_pages)
        for i in range(total_pages):
            if i == current_page:
                cols[i].button(f"{i + 1}", key=f"page_{i}", disabled=True)
            else:
                if cols[i].button(f"{i + 1}", key=f"page_{i}"):
                    st.session_state.current_page = i