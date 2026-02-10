import streamlit as st
import pandas as pd
import asyncio
import subprocess
import sys 
from vector_storage import get_matches
from job_scraper import scrape_dice_jobs 

st.set_page_config(page_title="Job Matcher", layout="wide")


def install_playwright_browser():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        print("Playwright browser installed")
    except Exception as e:
        print(f"Error installing browser {e}")

if "browser_installed" not in st.session_state:
    with st.spinner("Setting up browser engine... (This happens once)"):
        install_playwright_browser()
        st.session_state.browser_installed = True

st.title("Job Recommendations")
st.subheader("Matching")

with st.sidebar:
    st.header("Search Filters")
    num_results = st.slider("Number of matches to show", 1, 10, 5)
    
    if st.button("Refresh Database"):
        with st.status("Scraping Dice.com...", expanded=True) as status:
            st.write("Initializing browser...")
            try:

                asyncio.run(scrape_dice_jobs("Application Support", "New Jersey"))
                
                status.update(label="Scrape Complete!", state="complete", expanded=False)
                st.success("Database updated! Reloading matches...")
                st.rerun()
            except Exception as e:
                st.error(f"Scraper failed: {e}")

my_profile = "B.A. Computing and Informatics, Application Support, SQL, AWS, Python, Security+."

results = get_matches(my_profile, n_results=num_results)

if results and results['ids'] and results['ids'][0]:
    for i in range(len(results['ids'][0])):
        score = (1 - results['distances'][0][i]) * 100
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {results['metadatas'][0][i]['title']}")
                st.caption(f"Company: {results['metadatas'][0][i]['company']}")
                st.write(results['documents'][0][i][:300] + "...")
            with col2:
                st.metric("Match Quality", f"{score:.1f}%")
            st.divider()
else:
    st.info("No jobs found in database. Click 'Refresh Database' to start a search.")