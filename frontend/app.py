import os
import streamlit as st
from customers_data import display_customers
from candidates import show_google_drive_data # display_candidates
from messages import display_messages
from materials import display_materials
from dotenv import load_dotenv 

# Load the environment variables
load_dotenv()
TOKEN = os.getenv("STREAMLIT_TOKEN", "default_vigilantai_token")  # Change the default as needed
# Hide Streamlit menu and footer only
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Main logic for the Streamlit app
def main():
    # Initialize session state for token if not present
    if 'token' not in st.session_state:
        st.session_state.token = None

    # Check if the token is valid
    if st.session_state.token != TOKEN:
        # Create a token input field
        st.title("VigilantAI: Access Restricted")
        
        # Input for token
        input_token = st.text_input("Please enter your token to access the application.", type="password")
        
        if st.button("Submit"):
            if input_token == TOKEN:
                st.session_state.token = TOKEN  # Set token in session state if correct
                st.success("Access granted! Please reload to proceed.")
                st.rerun()  # Reload the page to clear the state
            else:
                st.error("Invalid token. Please try again.")
        return  # Stop further execution if the token is not valid

    # If the token is valid, show the main content
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Select a table", ['Email Messages', 'Customers', 'Candidate Leads', 'Materials'])

    if menu == 'Email Messages':
        display_messages(st, st.session_state.current_page)
    elif menu == 'Customers':
        display_customers(st, st.session_state.current_page)
    elif menu == 'Candidate Leads':
        show_google_drive_data(st, st.session_state.current_page)
        # display_candidates(st, st.session_state.current_page)
    elif menu == 'Materials':
        display_materials()

if __name__ == '__main__':
    main()