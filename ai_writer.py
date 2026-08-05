import google.generativeai as genai
import streamlit as st
import os

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def get_api_key():
    # Check Environment Variable first (Silences Pylance/Linter errors)
    env_key = os.getenv("GOOGLE_API_KEY")
    if env_key:
        return env_key
    
    # Check Streamlit Secrets (for Cloud Deployment)
    if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
        
    return None

def configure_model():
    api_key = get_api_key()
    if not api_key:
        # Stop the app gracefully if key is missing
        st.error("❌ GOOGLE_API_KEY not found. Please set it in .env or .streamlit/secrets.toml")
        return None
        
    genai.configure(api_key=api_key)
    # FIXED: Changed from 'gemini-2.5-flash' (invalid) to 'gemini-1.5-flash'
    return genai.GenerativeModel('gemini-2.5-flash')

def generate_application_materials(job_title, company, job_description, my_resume):
    try:
        model = configure_model()
        if not model: return "Error: API Key Missing"

        prompt = f"""
        ROLE: Expert Career Coach.
        TASK: Write a customized Cover Letter for Michael Morris.
        
        MY RESUME:
        {my_resume}
        
        JOB DESCRIPTION:
        Title: {job_title} at {company}
        {job_description}
        
        REQUIREMENTS:
        1. Keep it professional but energetic.
        2. Focus on connecting my 'Pick of Day Bot' and 'East Coast Jewels' work to their needs.
        3. Max 200 words.
        4. FORMATTING: Do NOT use bold text (asterisks). Plain text only.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def tailor_resume(job_title, company, job_description, my_resume):
    try:
        model = configure_model()
        if not model: return "Error: API Key Missing"

        model = configure_model()
        prompt = f"""
        ROLE: Expert Technical Resume Writer.
        TASK: Tailor Michael Morris's resume for a {job_title} role at {company}.
        
        CRITICAL RULES:
        1. TONE: DO NOT use "Junior", "Graduate", or "Immediately Available".
        2. STRUCTURE: Maintain the separation between "EXPERIENCE" (Employment) and "PROJECTS" (Dev work). Do NOT merge them.
        3. CONTENT: Use the "Pick of Day Bot" metrics (Stripe, AWS, NextAuth) to prove experience.
        4. SUMMARY: Start with "Technical Support Specialist" with experience...".
        5. FORMATTING: Output strict Markdown. No paragraphs in Experience/Projects, only bullets.
        6. SKILL SELECTION: Look at the Job Description. Select ONLY the top 20-25 skills from my resume that match their needs. DROP skills that are irrelevant to this specific role to save space.
        7. EXPERIENCE AND PROJECTS: It's okay to change the wording a bit to match the job description.
        
        MY RESUME:
        {my_resume}
        
        TARGET JOB:
        Title: {job_title} at {company}
        Description: {job_description}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"