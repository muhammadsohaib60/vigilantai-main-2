from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import json
import base64
import os
import libgenai 

# Constants for Google Drive API
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
MATERIALS_FOLDER = os.getenv("MATERIALS_FOLDER")
FILES_PER_PAGE = 10

encoded_creds = os.getenv('VIGILANTAI_SERVICE_ACCOUNT_KEY')
decoded_creds = base64.b64decode(encoded_creds)
service_account_info = json.loads(decoded_creds)

# Mapping MIME types to human-readable formats
MIME_TYPE_MAP = {
    'application/pdf': 'PDF',
    'application/msword': 'DOC',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
    'application/vnd.ms-excel': 'XLS',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX',
    'application/vnd.ms-powerpoint': 'PPT',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPTX',
    'image/jpeg': 'JPEG Image',
    'image/png': 'PNG Image',
    'text/plain': 'Text File',
    # Add other relevant MIME types as needed
}

# Function to get Google Drive file list
def get_google_drive_files():
    #credentials = service_account.Credentials.from_service_account_file(
    #    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    scoped_credentials = credentials.with_scopes(SCOPES)
    drive_service = build('drive', 'v3', credentials=scoped_credentials)

    # Query files from the folder
    results = drive_service.files().list(
        q=f"'{MATERIALS_FOLDER}' in parents",
        fields="files(id, name, mimeType, size)"
    ).execute()
    items = results.get('files', [])

    return items

# Function to map MIME types to human-readable types
def get_human_readable_file_type(mime_type):
    return MIME_TYPE_MAP.get(mime_type, 'Unknown File Type')

# Background function for reindexing
def reindex_materials():
    libgenai.materials_reindex()
    st.session_state.reindex_done = True  # Set the state as done

# Function to display files in Streamlit with numbered pagination
def display_materials():
    # Get the file list from Google Drive
    files = get_google_drive_files()

    if not files:
        st.write("No files found.")
        return

    # Initialize or update pagination state
    if 'materials_page' not in st.session_state:
        st.session_state.materials_page = 0

    # Calculate the total number of pages
    total_files = len(files)
    total_pages = (total_files - 1) // FILES_PER_PAGE + 1

    # Display files for the current page
    start_index = st.session_state.materials_page * FILES_PER_PAGE
    end_index = start_index + FILES_PER_PAGE
    page_files = files[start_index:end_index]

    # Reindex button and logic
    if st.button("Reindex all materials") and not st.session_state.get('reindexing', False):
        st.session_state.reindexing = True
        st.session_state.reindex_done = False
        reindex_materials()
        st.rerun()

    # Show reindexing completion message if done
    if st.session_state.get('reindex_done', False):
        st.success("Reindexing successfully done.")
        st.session_state.reindexing = False
 
    # Prepare data for the table with continuous numbering
    data = []
    for i, file in enumerate(page_files):
        file_name = file.get('name')
        file_type = get_human_readable_file_type(file.get('mimeType'))
        file_size = file.get('size', 'Unknown')  # Default to 'Unknown' if size is not available
        continuous_index = start_index + i + 1  
        data.append([continuous_index, file_name, file_type, file_size])

    # Convert to a DataFrame for tabular display
    df = pd.DataFrame(data, columns=['#', 'File Name', 'Type', 'Size (bytes)']) 
    st.dataframe(df, hide_index=True)

    # Display numbered pagination controls horizontally
    st.write("Page:")
    cols = st.columns(total_pages)  # Create a column for each page
    for i in range(total_pages):
        with cols[i]:
            if st.button(str(i + 1), key=f"page_{i + 1}"):
                st.session_state.materials_page = i  # Set the current page based on button click

    # Display the current page number
    st.write(f"Showing page {st.session_state.materials_page + 1} of {total_pages}")
