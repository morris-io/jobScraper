import streamlit as st
import google.generativeai as genai
import os

# This works locally from secrets.toml AND in the cloud from the dashboard
if "GOOGLE_API_KEY" in st.secrets:
    OS_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Fallback for local testing if not using st.secrets
    OS_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=OS_API_KEY)

resume_text = """
Michael J. Morris - Technical Support Engineer & System Reliability Specialist.
Education: Bachelor's in Computing and Informatics, Rowan University (2025).
Relevant Coursework: CompTIA Security+ Prep, CompTIA CYSA+ Prep, Splunk Cloud Admin Prep.

Core Skills: 
Technical Support, System Reliability, Log Analysis, Incident Response, Database Maintenance, 
SQL, REST API Debugging, Cloud Operations (AWS EC2/S3, Vercel), MongoDB, NextAuth.js.

Experience:
- Web Support Specialist (East Coast Jewels): Diagnosing platform errors, resolving payment 
  gateway disputes (Stripe), and UI/UX regression testing.
- Full-Stack Developer: Built 'Pick of Day Bot' (SaaS) and 'Fantasy Fairway'. 
  Experienced in serverless backends, automated cron jobs, and CI/CD pipelines.

Certifications: 
TryHackMe Pre-Security Learning Path (2026).
"""

def generate_embedding(text):
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_query"
    )
    return result['embedding']

try:
    resume_vector = generate_embedding(resume_text)
    print("Generated resume vector")
    print(f"Vector Dimension: {len(resume_vector)}")
    print(f"Sample (First 3 values): {resume_vector[:3]}")
    
except Exception as e:
    print(f"Error embedding: {e}")