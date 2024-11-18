import pandas as pd
import random
import requests
import json
import os
import time
import messages
from bs4 import BeautifulSoup
from app_utils import paginate_data, display_pagination
from selenium import webdriver

PAGE_SIZE = 50
FOLDER_ID = os.getenv("FOLDER_ID")
CANDIDATES_FILE = "candidates.csv"

# Streamlit app to display CSV data
def show_google_drive_data(st, current_page):
    st.title("Candidates Table")

    # Button to load the file
    data = messages.load_google_drive_csv(FOLDER_ID, CANDIDATES_FILE)
    # Button to generate new data
    if st.button("Generate New Data"):
        with st.spinner("Generating new data..."):
            generate_candidates_data()  # Call the data generation function
            st.success("Data generation completed successfully!")

        # Reload the updated data from Google Drive after generation
        data = messages.load_google_drive_csv(FOLDER_ID, CANDIDATES_FILE)

    # Button to renew ratings (does nothing for now)
    if st.button("Renew rating info"):
        renew_ratings()  # Call the renew ratings function
        st.info("Rating information renewal done.")

    # Display the data in the dataframe
    if data is not None:
        # Reorder and rename columns
        data = data[['name', 'rating', 'state', 'address', 'link']]
        data = data.rename(columns={'state': 'city'})  # Rename 'state' to 'city'
        # Convert 'rating' column to integer
        # Convert 'rating' column to integer safely
        data['rating'] = pd.to_numeric(data['rating'], errors='coerce').fillna(0).astype(int)
        st.dataframe(data)  # Display the CSV content in a table
    else:
        st.error("Error loading the file. Please check folder ID and file name.")


# Generate an empty DataFrame with the same columns as before
def generate_candidates_data():
    # Start the data fetching from "from=0" to "from=2000"
    all_hospitals = []
    for offset in range(0, 2001, 50):
        # Define the URL with the "from" parameter adjusted for each iteration
        url = f"https://ratings.leapfroggroup.org/rest/search/results?distance=any&address=10%20Richards%20Rd%20%23110%2C%20Kansas%20City%2C%20MO%2064116%2C%20United%20States&coords=39.1153551%2C-94.5916469&by=distance&sort=distance&from={offset}&size=50"
        
        # Call the function to get hospital data
        hospitals = get_hospital_data(url)
        
        # Append hospitals data to the complete list
        all_hospitals.extend(hospitals)
        
        # Sleep for 1 second between requests
        time.sleep(1)

    # Create a DataFrame with the hospital data
    df = pd.DataFrame(all_hospitals, columns=['name', 'link', 'address', 'state'])
    messages.save_google_drive_csv(FOLDER_ID, CANDIDATES_FILE, df)
    
    return df

# Display candidates and handle empty data
def display_candidates(st, current_page):
    st.title("Candidates Table")
    data = generate_candidates_data()
    
    if data.empty:
        st.warning("No data loaded")
        st.dataframe(data, height=400)  # Display an empty table with correct columns
    else:
        total_pages = (len(data) + PAGE_SIZE - 1) // PAGE_SIZE
        paginated_data = paginate_data(data, current_page, PAGE_SIZE)
        
        st.dataframe(paginated_data, height=400)
        display_pagination(st, total_pages, current_page)

# Example pagination function (you'll need this to handle pagination)
def paginate_data(data, page, page_size):
    start = page * page_size
    end = start + page_size
    return data.iloc[start:end]

# Example pagination display function
def display_pagination(st, total_pages, current_page):
    if current_page > 0:
        if st.button("Previous"):
            current_page -= 1
    if current_page < total_pages - 1:
        if st.button("Next"):
            current_page += 1


def get_hospital_data(url):
    # Fetch data from the URL
    response = requests.get(url)
    data = response.json()
    hospitals = []
    
    # Loop through each result in the JSON response
    for item in data.get('markup', '').split('<tr class='):
        if 'declined-survey' in item:
            continue  # Skip rows where the hospital has declined the survey
        
        soup = BeautifulSoup(item, 'html.parser')

        # Extract hospital name
        name_tag = soup.find('div', class_='name')
        name = name_tag.text.strip() if name_tag else None

        # Extract link
        link_tag = soup.find('a', class_='with-return-query')
        link = link_tag['href'] if link_tag else None

        # Extract address and state
        address_tag = soup.find('div', class_='address')
        if address_tag:
            address = address_tag.get_text(separator=", ").strip()
            # Extract state by splitting address
            state = address.split(',')[-2].strip() if ',' in address else None
        else:
            address, state = None, None
        
        # Store the result
        if name and link and address:
            hospitals.append({
                'name': name,
                'link': link,
                'address': address,
                'state': state
            })
    
    return hospitals

def renew_ratings():
    # Step 1: Load the CSV data from Google Drive
    data = messages.load_google_drive_csv(FOLDER_ID, CANDIDATES_FILE)
    
    if data is None or data.empty:
        return

    # Step 2: Check if the 'rating' column exists
    if 'rating' not in data.columns:
        data['rating'] = 0  # Initialize 'rating' column
    
    # Ensure the directory for HTML files exists
    # os.makedirs("saved_html", exist_ok=True)

    # Initialize the WebDriver (e.g., Chrome)
    driver = webdriver.Chrome()  # Ensure you have ChromeDriver installed and in PATH

    # Step 3: Iterate through each link in the 'link' column to extract the rating
    for index, row in data.iterrows():
        if index > 550:
            break
        rating_metric = row.get('rating', 0)
        if rating_metric in {"1.0", "2.0", "3.0", "4.0"} or index < 350:
            print("++++++++++++++++++++++++++++ SKIP +++++++++++++++++++++++++++")
            continue
        else:
            print(rating_metric)
            link = row.get('link')
            hospital_name = row.get('name', 'Unknown')  # Adjust this if necessary

            if link:
                try:
                    # Open the page with Selenium
                    driver.get(link)
                    time.sleep(10)  # Wait for 1 second to ensure content is fully loaded
                    print(link)
                    
                    # Get the page content
                    page_content = driver.page_source

                    # Save the page content to an HTML file
                    # html_filename = f"saved_html/{hospital_name.replace(' ', '_')}_{index}.html"
                    # with open(html_filename, "w", encoding="utf-8") as file:
                    #     file.write(page_content)
            
                    # Parse the HTML content
                    soup = BeautifulSoup(page_content, 'html.parser')
                    
                    # Find the 'td' with class 'name' containing "Infection in the Blood"
                    infection_name_td = soup.find("td", class_="name", string="Infection in the Blood")
                    
                    # Ensure we find the correct row by looking for its parent 'tr'
                    if infection_name_td:
                        # Access the sibling 'td' with class 'progress' in the same row
                        progress_td = infection_name_td.find_next_sibling("td", class_="progress")
                        img_tag = progress_td.find("img")
                        
                        if img_tag and 'icon-measure' in img_tag['src']:
                            # Extract the rating value before the dash
                            rating_text = float(img_tag['src'].split('-')[-2])  # Gets the first number as rating
                            data.at[index, 'rating'] = rating_text

                            # Print iteration number, hospital name, and rating
                            print(f"Iteration {index + 1}: {hospital_name} - Rating Parsed: {rating_text}")
                        else:
                            print(f"No rating image found for 'Infection in the Blood' in {hospital_name}")
                    else:
                        print(f"Iteration {index + 1} 'Infection in the Blood' entry not found in {hospital_name} within {link}")
                    
                    # Wait for 1 second before the next request
                    # time.sleep(1)

                except Exception as e:
                    print(f"Error fetching {link} for {hospital_name}: {e}")
                    data.at[index, 'rating'] = 'Error'

    # Step 4: Save the updated DataFrame back to the CSV in Google Drive
    messages.save_google_drive_csv(FOLDER_ID, CANDIDATES_FILE, data)
    
    # Close the WebDriver
    driver.quit()
    
    return True