import time
import streamlit as st

# Utility functions shared across files
def paginate_data(data, page, page_size):
    return data.iloc[page * page_size:(page + 1) * page_size]

def display_pagination(st, total_pages, current_page):
    cols = st.columns(total_pages)
    for i in range(total_pages):
        if i == current_page:
            cols[i].button(f"{i + 1}", key=f"page_{i}", disabled=True)
        else:
            if cols[i].button(f"{i + 1}", key=f"page_{i}"):
                st.session_state.current_page = i

def simulate_reindexing(st):
    with st.spinner('Re-indexing...'):
        time.sleep(2)
    st.success('Re-indexing completed.')

