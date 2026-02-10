import streamlit as st
import pandas as pd
from vector_storage import get_matches 

st.set_page_config(page_title="Job Matcher", layout="wide")

st.title("Job Recommendations")
st.subheader("Matching")

with st.sidebar:
    st.header("Search Filters")
    num_results = st.slider("Number of matches to show", 1, 10, 5)
    if st.button("Refresh Database"):
        st.info("New scrape...") 

my_profile = "B.A. Computing and Informatics, Application Support, SQL, AWS, Python."

results = get_matches(my_profile, n_results=num_results)

if results['ids'][0]:
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
    st.write("No jobs found. Run the scraper")