import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import os
import libgenai 
from dotenv import load_dotenv
import base64
import json
import time

# Constants
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = os.getenv("FOLDER_ID")
SOURCE_CSV_FILE_NAME = os.getenv("SOURCE_FILE")
DESTINATION_CSV_FILE_NAME = os.getenv("DESTINATION_FILE")
PAGE_SIZE = 20

encoded_creds = os.getenv('VIGILANTAI_SERVICE_ACCOUNT_KEY')
decoded_creds = base64.b64decode(encoded_creds)
service_account_info = json.loads(decoded_creds)

# Function to authenticate Google Drive
def get_credentials():
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    scoped_credentials = credentials.with_scopes(SCOPES)
    service = build('drive', 'v3', credentials=scoped_credentials)
    return service

# Function to load CSV from Google Drive
def load_google_drive_csv(folder_id, file_name):
    service = get_credentials()
    query = f"'{folder_id}' in parents and name='{file_name}'"
    response = service.files().list(q=query, fields="files(id, name)").execute()
    files = response.get('files', [])
    
    if not files:
        return None
    
    file_id = files[0]['id']
    request = service.files().get_media(fileId=file_id)
    file_path = f"/tmp/{file_name}"  # Temporary file path
    with open(file_path, "wb") as file:
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    
    return pd.read_csv(file_path)

# Function to save CSV to Google Drive
def save_google_drive_csv(folder_id, file_name, df):
    service = get_credentials()
    file_path = f"/tmp/{file_name}"  # Save the CSV locally first
    df.to_csv(file_path, index=False)

    # Get file ID if it exists
    query = f"'{folder_id}' in parents and name='{file_name}'"
    response = service.files().list(q=query, fields="files(id, name)").execute()
    files = response.get('files', [])
    
    if files:
        file_id = files[0]['id']
        media = MediaFileUpload(file_path, mimetype='text/csv')
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, mimetype='text/csv')
        service.files().create(body=file_metadata, media_body=media).execute()

# Function to save CSV to Google Drive 
# Destination
def fetch_and_save_parsed_csv_to_drive():
    # Load the CSV from Google Drive
    df = load_google_drive_csv(FOLDER_ID, SOURCE_CSV_FILE_NAME)
    
    # Iterate over each row and append the content as a new column
    for index, row in df.iterrows():
        # Generate the prompt
        #prompt = f"Hospital name: {row.iloc[0]}, Representative Title: {row.iloc[3]}, Address: {row.iloc[7]}, {row.iloc[8]}, {row.iloc[9]}, number of operating rooms: {row.iloc[10]}, number of beds: {row.iloc[11]}, Electronic Medical Record: {row.iloc[12]}"
        prompt = f"Hospital name: {row.iloc[3]}, Representative Title: {row.iloc[2]}, Address: {row.iloc[4]}, {row.iloc[5]}, {row.iloc[6]}, {row.iloc[8]}, follow-up: {row.iloc[13]}"
        
        # Perform similarity search
        results = libgenai.similarity_search(prompt)
        content = results[0].page_content
        
        # Append the content as a new column for the current row
        person = row.iloc[0] + " " + row.iloc[1]
        msg = libgenai.generate_proposition(content[:8000], person, row.iloc[3], row.iloc[2], {row.iloc[13]})
        print("###########################")
        # print(msg)
        df.at[index, 'Message Body'] = msg
        time.sleep(1)

    # Save the updated DataFrame back to Google Drive
    save_google_drive_csv(FOLDER_ID, DESTINATION_CSV_FILE_NAME, df)

    print("Parsed data saved to Google Drive successfully.")

# Function to regenerate destination.csv
def regenerate_customers(st):
    # fetch_and_parse_csv_from_drive()
    fetch_and_save_parsed_csv_to_drive()
    st.success(f"{DESTINATION_CSV_FILE_NAME} regenerated and saved to Google Drive.")

# Function to display messages table
# Function to display messages table
def display_messages(st, current_page):
    # Add the regenerate button at the top
    if st.button('Regenerate for current customers'):
        regenerate_customers(st)

    # Set the page title
    st.title("Messages Table")

    # Load the destination.csv data from Google Drive
    data = load_google_drive_csv(FOLDER_ID, DESTINATION_CSV_FILE_NAME)
    
    if data is None:
        st.error("Could not load data.")
        return

    # Add a download button for the full dataset
    csv_data = data.to_csv(index=False)
    st.download_button(
        label="Download Full Dataset",
        data=csv_data,
        file_name=DESTINATION_CSV_FILE_NAME,
        mime="text/csv"
    )

    # Display messages in a paginated format
    total_pages = (len(data) + PAGE_SIZE - 1) // PAGE_SIZE  # Calculate total pages
    paginated_data = data.iloc[current_page * PAGE_SIZE:(current_page + 1) * PAGE_SIZE]

    for i, row in paginated_data.iterrows():
        # Display full message without truncation
        full_message = row['Message Body']

        st.write(f"**Hospital Name:** {row['Company']} | **Representative:** {row['FirstName']} {row['LastName']} | **State:** {row['StateCode']}")
        formatted_message = format_email_message(full_message)
        for paragraph in formatted_message:
            st.write(paragraph)
        st.write("---")

    # Display pagination
    cols = st.columns(total_pages)
    for i in range(total_pages):
        if i == current_page:
            cols[i].button(f"{i + 1}", key=f"page_{i}", disabled=True)
        else:
            if cols[i].button(f"{i + 1}", key=f"page_{i}"):
                st.session_state.current_page = i


# Helper function to format an email message
def format_email_message(message):
    paragraphs = [p.strip() for p in message.split('\n\n') if p.strip()]
    return paragraphs

def fetch_and_parse_csv_from_drive():
    df = load_google_drive_csv(FOLDER_ID, SOURCE_CSV_FILE_NAME)
    
    for index, row in df.iterrows():
        prompt = f"Hospital name: {row.iloc[0]}, Representative Title: {row.iloc[3]}, Address: {row.iloc[7]}, {row.iloc[8]}, {row.iloc[9]}, number of operating rooms: {row.iloc[10]}, number of beds: {row.iloc[11]}, Electronic Medical Record: {row.iloc[12]}"
        results = libgenai.similarity_search(prompt)
        print(results[0].page_content[:50])

    return
