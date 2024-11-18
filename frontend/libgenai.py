import pandas as pd
import vertexai
from googleapiclient.discovery import build
from google.cloud import firestore
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from langchain_googledrive.document_loaders import GoogleDriveLoader
from langchain_google_firestore import FirestoreVectorStore
from langchain_google_vertexai import VertexAIEmbeddings
from langchain.schema import Document
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv
import os
import base64
import json
import tempfile

load_dotenv()
# Path to your OAuth 2.0 client credentials
MATERIALS_FOLDER = os.getenv("MATERIALS_FOLDER")
FIREBASE_COLLECTION = "secondaryemail"
PROJECT_ID = os.getenv('PROJECT_ID')
DOCUMENTS_NUM_INDEX = 200
GCP_REGION="europe-west4"

encoded_creds = os.getenv('VIGILANTAI_SERVICE_ACCOUNT_KEY')
decoded_creds = base64.b64decode(encoded_creds)
service_account_info = json.loads(decoded_creds)

CREDENTIALS = service_account.Credentials.from_service_account_info(service_account_info)
# Save the decoded credentials to a temporary JSON file
with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_creds_file:
    temp_creds_file.write(decoded_creds)
    temp_creds_file_path = temp_creds_file.name
# CREDENTIALS = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

def initialize_firestore():
    return firestore.Client(credentials=CREDENTIALS)


def materials_reindex():
    load_drive()
    print("reindexed folder")

    return 

def request_embedding(text):
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    vector = model.get_embeddings([text])

    return vector[0].values

def load_drive():
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    loader = GoogleDriveLoader(
        folder_id=MATERIALS_FOLDER,
        recursive=False,
        credentials_path=temp_creds_file_path,
        num_results=DOCUMENTS_NUM_INDEX,  # Maximum number of file to load
    )

    files = loader.load()
    # ids = []
    # contents = []

    #for document in files:
        #part1, part2, part3 = split_gdrive_url(document.metadata["source"])
        #ids.append(part2)
        #contents.append(document.page_content)
        #vector = model.get_embeddings([document.page_content])
        #save_vectorized_data_to_firestore(part2, vector[0].values, document.page_content)

    save_native_vectors_to_firestore(files)

    return

# Function to save vectors to Firestore in Langchain Native
def save_native_vectors_to_firestore(files):
    # truncate_collection()
    embedding = VertexAIEmbeddings(
        model_name="text-embedding-004",
        project=PROJECT_ID
    )

    CLIENT = initialize_firestore()

    vector_store = FirestoreVectorStore.from_documents(
        collection=FIREBASE_COLLECTION,
        documents=files,
        embedding=embedding,
        client=CLIENT
    )

    return


# Function to save vectorized data and related content to Firestore
def save_vectorized_data_to_firestore(document_id, vectors, content):
    """
    Saves vectorized data (from text content) and related content to Firestore.
    
    Args:
        collection_name (str): Firestore collection name.
        document_id (str): Document ID under which the data will be saved.
        text_content (str): The text content to vectorize and store.
        related_content (dict): Other related content to store (e.g., metadata, original text, etc.).
        
    Returns:
        dict: Firestore response on successful save.
    """

    # Initialize Firestore client
    db = initialize_firestore()
    
    # Prepare the document data
    document_data = {
        'vectorized_data': vectors,  
        'text_content': content,
        'document': document_id
    }

    # Reference the Firestore collection and document
    doc_ref = db.collection(FIREBASE_COLLECTION).document(document_id)

    # Save the data to Firestore
    try:
        doc_ref.set(document_data)
        print(f"Document {document_id} successfully written to {FIREBASE_COLLECTION}.")
        return {"status": "success", "document_id": document_id}
    except Exception as e:
        print(f"An error occurred while writing to Firestore: {e}")
        return {"status": "error", "message": str(e)}

# Function to get documents from Google Drive folder
def get_google_drive_documents():
    """
    Retrieve documents from a Google Drive folder using service account credentials.
    
    Args:
        folder_id (str): The Google Drive folder ID.
        service_account_file (str): Path to the service account JSON file.
    
    Returns:
        List[Document]: List of LangChain Document objects containing the content and metadata.
    """
    folder_id = MATERIALS_FOLDER
    # service_account_file = SERVICE_ACCOUNT_FILE

    # Authenticate using service account credentials
    # credentials = service_account.Credentials.from_service_account_file(service_account_file)
    drive_service = build('drive', 'v3', credentials=CREDENTIALS)

    # List all files in the folder
    query = f"'{folder_id}' in parents"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    documents = []
    
    for file in files:
        file_id = file.get('id')
        file_name = file.get('name')
        print(file_name)

        #doc = Document(page_content=pdf_content, metadata={"source": file_name})
        #documents.append(doc)

    return # documents

# Index data from a Google Drive folder
def load_gdrive_folder():
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    loader = GoogleDriveLoader(
        service_account_key=SERVICE_ACCOUNT_FILE,
        folder_id=MATERIALS_FOLDER,
        recursive=False,
        num_results=10
    ) 

    files = loader.load()
    print(files)
    for document in files:
        print(document.page_content[:50])
        # vector = model.get_embeddings([document.page_content])
        # collection.add(
        #     documents=[document.page_content],
        #     embeddings=[vector[0].values],
        #     metadatas=[document.metadata],
        #     ids=[document.metadata["source"]]
        # )

    return

def split_gdrive_url(url):
    # Define the prefix to split before the document ID
    prefix = "https://docs.google.com/document/d/"
    
    # Ensure the URL starts with the prefix
    if not url.startswith(prefix):
        raise ValueError("URL format is not as expected.")
    
    # Remove the prefix from the URL to isolate the document ID and the rest
    remaining_url = url[len(prefix):]
    
    # Split the remaining URL into document ID and the rest
    doc_id, rest = remaining_url.split('/', 1)
    
    # Return the three parts: prefix, document ID, and the rest
    return prefix, doc_id, rest

# Function to get all document IDs from the Firestore collection
def truncate_collection():
    # Reference to the collection
    db = initialize_firestore()
    collection_ref = db.collection(FIREBASE_COLLECTION)
    
    # Get all documents in the collection
    docs = collection_ref.stream()

    # Iterate over each document and delete it
    for doc in docs:
        print(f"Deleting document with ID: {doc.id}")
        collection_ref.document(doc.id).delete()

    print(f"All documents from '{FIREBASE_COLLECTION}' have been deleted.")

# Function to find similarity
def similarity_search(prompt):
    vertexai.init(credentials=CREDENTIALS, project=PROJECT_ID, location=GCP_REGION)
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    vector = model.get_embeddings([prompt])

    embedding = VertexAIEmbeddings(
        model_name="text-embedding-004",
        project=PROJECT_ID,
        credentials=CREDENTIALS
    )

    CLIENT = initialize_firestore()

    vector_store = FirestoreVectorStore(
        collection=FIREBASE_COLLECTION,
        embedding_service=embedding,
        client=CLIENT
    )

    result = vector_store.similarity_search_by_vector(vector[0].values)

    return result

def generate_proposition(document, person, hospital, title, followup):
    # Initialize the AI Platform client
    vertexai.init(credentials=CREDENTIALS , project=PROJECT_ID, location=GCP_REGION)

    # model = GenerativeModel("gemini-1.5-pro")
    model = GenerativeModel("gemini-1.0-pro-002")

    prompt_template = os.getenv("EMAIL_PROMPT")
    # recommendation_template = os.getenv("EMAIL_PROMPT_RECOMMENDATION")
    prompt = prompt_template.format(person=person, title=title, hospital=hospital, document=document, followup=followup)
    # print(prompt)
    #recommendation_text = recommendation_template.format(recommendation=recommendation)

    # Generate content using the model
    #response = model.generate_content(prompt)

    #return response.text # + recommendation_text 

    try:
        # Generate content using the model
        response = model.generate_content(prompt)
        return response.text
    except Exception:  # Replace with the specific exception for content filter errors
        # Return an empty string if content filtering error occurs
        return ""