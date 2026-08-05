import streamlit as st
import pandas as pd
import asyncio
import subprocess
import sys 
import os
import re
import markdown
from pypdf import PdfReader
from io import BytesIO
from xhtml2pdf import pisa
from vector_storage import get_matches
# CHANGED: Importing the new LinkedIn keyword scraper
from job_scraper import scrape_linkedin_keywords, scrape_linkedin_remote_helpdesk, scrape_single_url 
from ai_writer import generate_application_materials, tailor_resume

st.set_page_config(page_title="Job Matcher", layout="wide")

# --- 1. CONFIGURATION: YOUR FULL SKILL LIST ---
# The app will scan job descriptions for these exact keywords
MY_TECH_STACK = [
    # Dev / App Support
    "JavaScript", "TypeScript", "React", "Node", "SQL", "AWS", 
    "Python", "API", "Linux", "Splunk", "Mongo", "Stripe", 
    "Next.js", "CI/CD", "Git", "Troubleshooting", "Ticket",
    "Application Support", "Log Analysis", "CLI", "Server Configuration",
    "Systems Analysis", "ITIL", "Debugging", "Database Maintenance",
    "IAM", "Cloud Computing", "Kubernetes", "Network Security",
    "DNS", "HTTPS", "Wireshark", "Networking", "VPN",
    # Help Desk / IT Support
    "Help Desk", "Helpdesk", "Service Desk", "Desktop Support",
    "Tier 1", "Tier 2", "Tier1", "Tier2", "Remote Support",
    "Active Directory", "Office 365", "Microsoft 365", "Windows",
    "macOS", "Ticketing System", "ServiceNow", "Jira", "Zendesk",
    "Hardware", "Software Installation", "Password Reset",
    "VoIP", "Incident Management", "SLA", "End User Support",
    "Technical Support", "IT Support", "CompTIA", "A+"
]

def extract_keywords(description):
    found = []
    # Create a giant regex pattern: (\bJava\b|\bSQL\b|...)
    # \b ensures we only match whole words
    escaped_skills = [re.escape(s) for s in MY_TECH_STACK]
    pattern = r'\b(' + '|'.join(escaped_skills) + r')\b'
    
    matches = re.findall(pattern, description, re.IGNORECASE)
    # Normalize matches to the original casing in MY_TECH_STACK if needed, 
    # or just return unique set of what was matched
    return list(set([m.title() for m in matches]))

# --- 2. RESUME FUNCTIONS ---
def load_resume():
    try:
        with open("resume.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: resume.txt not found. Please create it!"

RESUME_CONTEXT = load_resume()

def safe_filename(company_name):
    clean = re.sub(r'[^a-zA-Z0-9_\- ]', '', company_name)
    clean = clean.replace('\n', ' ').strip()
    return clean[:30]

# --- 3. PDF GENERATORS (EXACTLY AS YOU PROVIDED) ---
def create_pdf(markdown_text):
    # --- 1. PRE-CLEANING ---
    text = markdown_text.replace("```markdown", "").replace("```", "").strip()
    
    # GLOBAL SANITIZATION
    # Remove bold markers because we apply bolding manually
    text = text.replace("**", "").replace("__", "")

    # Isolate the Body
    if "PROFESSIONAL SUMMARY" in text:
        text = text[text.find("PROFESSIONAL SUMMARY"):]

    # Fix "Present" formatting
    text = re.sub(r'(\d{4})\s*\n\s*(Present)', r'\1 - \2', text)
    text = re.sub(r'(March|April|May|June|July|Aug|Sept|Oct|Nov|Dec)\s+(\d{4})\s*\n\s*(Present)', r'\1 \2 - \3', text)

    # --- 2. CUSTOM PARSER ---
    html_lines = []
    
    # Hardcoded Header
    html_lines.append("""
        <div class="header-name">Michael J. Morris</div>
        <div class="contact-line">Wildwood, NJ | 609-665-4737 | mchaelmorris@gmail.com | michaeljackmorris.com</div>
    """)

    lines = text.split('\n')
    in_list = False
    current_section = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # HEADERS
        if line.startswith("##") or line.upper() in ["PROFESSIONAL SUMMARY", "EXPERIENCE", "PROJECTS", "EDUCATION", "SKILLS", "CERTIFICATIONS"]:
            if in_list: 
                html_lines.append("</ul>")
                in_list = False
            
            clean_header = line.replace("#", "").strip()
            current_section = clean_header
            html_lines.append(f"<h2>{clean_header}</h2>")

        # JOB TITLES (contain a pipe |)
        elif "|" in line and ("Present" in line or "20" in line):
            if in_list: 
                html_lines.append("</ul>")
                in_list = False
            clean_line = line.replace("*", "").strip()
            if clean_line.endswith("|"):
                clean_line = clean_line[:-1].strip()
            html_lines.append(f'<div class="job-title">{clean_line}</div>')

        # SKILLS / KEY-VALUE PAIRS (The Fix for "* Tools:" and "* Relevant Coursework:")
        # We check for a colon, but we also STRIP the weird characters from the "Key"
        elif ":" in line and len(line) < 300: 
            if in_list: 
                html_lines.append("</ul>")
                in_list = False
            
            parts = line.split(":", 1)
            # CLEAN THE CATEGORY NAME: Remove *, -, • from the start
            category = parts[0].replace("*", "").replace("-", "").replace("•", "").strip()
            skills = parts[1].strip()
            html_lines.append(f'<p class="skill-line"><b>{category}:</b> {skills}</p>')

        # BULLETS (start with - or * or •)
        elif line.startswith("-") or line.startswith("*") or line.startswith("•"):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            clean_content = line.lstrip("-*• ").strip()
            html_lines.append(f"<li>{clean_content}</li>")

        # REGULAR TEXT (Summaries, Certifications)
        else:
            if in_list: 
                html_lines.append("</ul>")
                in_list = False
            # Clean generic text of leading bullets just in case
            clean_line = line.lstrip("-*• ").strip()
            html_lines.append(f"<p>{clean_line}</p>")

    if in_list:
        html_lines.append("</ul>")

    body_html = "\n".join(html_lines)

    # --- 3. STRICT CSS ---
    full_html = f"""
    <html>
    <head>
        <style>
            @page {{
                size: letter;
                margin: 0.4in;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 9pt;
                color: #000000;
                line-height: 1.3;
            }}
            .header-name {{
                text-align: center;
                text-transform: uppercase;
                font-size: 18pt;
                font-weight: bold;
                margin-bottom: 2px;
            }}
            .contact-line {{
                text-align: center;
                font-size: 9pt;
                margin-bottom: 10px;
                border-bottom: 1px solid #000000;
                padding-bottom: 4px;
            }}
            h2 {{
                font-size: 10pt;
                font-weight: bold;
                text-transform: uppercase;
                border-bottom: 1px solid #999999;
                margin-top: 10px;
                margin-bottom: 4px;
            }}
            .job-title {{
                font-weight: bold;
                margin-top: 6px;
                margin-bottom: 2px;
            }}
            ul {{
                margin-top: 0px;
                margin-bottom: 0px;
                padding-left: 15px;
            }}
            li {{
                margin-bottom: 1px;
                text-align: justify;
            }}
            p {{
                margin-top: 2px;
                margin-bottom: 2px;
                text-align: justify;
            }}
            .skill-line {{
                margin-bottom: 3px;
            }}
            b {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        {body_html}
    </body>
    </html>
    """
    
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(full_html, dest=pdf_buffer)
    
    if pisa_status.err:
        return None
    return pdf_buffer.getvalue()

def create_cover_letter_pdf(letter_text):
    # 1. Standard Header (Matches Resume)
    header_html = """
    <div class="header-name">Michael J. Morris</div>
    <div class="contact-line">Wildwood, NJ | 609-665-4737 | mchaelmorris@gmail.com | michaeljackmorris.com</div>
    """

    # 2. Convert Text to HTML
    # We use simple Markdown parsing because letters are just paragraphs
    body_html = markdown.markdown(letter_text)

    # 3. Apply Professional Styling (Matching Resume Font/Margins)
    full_html = f"""
    <html>
    <head>
        <style>
            @page {{
                size: letter;
                margin: 1.0in; /* Standard cover letter margins are wider (1 inch) */
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 11pt; /* Slightly larger font for readability */
                color: #000000;
                line-height: 1.5; /* Standard business letter spacing */
            }}
            .header-name {{
                text-align: center;
                text-transform: uppercase;
                font-size: 18pt;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .contact-line {{
                text-align: center;
                font-size: 10pt;
                margin-bottom: 40px; /* Space between header and "Dear Hiring Manager" */
                border-bottom: 1px solid #000000;
                padding-bottom: 10px;
            }}
            p {{
                margin-bottom: 15px;
                text-align: justify;
            }}
        </style>
    </head>
    <body>
        {header_html}
        {body_html}
    </body>
    </html>
    """
    
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(full_html, dest=pdf_buffer)
    
    if pisa_status.err:
        return None
    return pdf_buffer.getvalue()

def install_playwright_browser():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"Browser install error: {e}")

if "browser_installed" not in st.session_state:
    install_playwright_browser()
    st.session_state.browser_installed = True

st.title("Job Matcher")

mode = st.radio("Select Mode:", ["Search Database", "🔗 Direct Link Analysis", "📄 Upload Job PDF"], horizontal=True)

if mode == "📄 Upload Job PDF":
    st.info("Upload a job description PDF (like a State/Gov posting) to generate materials.")
    
    col_upload, col_details = st.columns([2, 1])
    with col_upload:
        uploaded_file = st.file_uploader("Upload Job PDF", type="pdf")
    with col_details:

        manual_title = st.text_input("Job Title:", value="Information Technology Specialist")
        manual_company = st.text_input("Company/Agency:", value="State of New Jersey")

    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        pdf_text = ""
        for page in reader.pages:
            pdf_text += page.extract_text() + "\n"
        
        found_skills = extract_keywords(pdf_text)
        
        st.divider()
        st.markdown(f"## {manual_title}")
        st.caption(f"Company: {manual_company}")
        
        if found_skills:
            st.success(f"🔥 **Skills Detected:** {', '.join(found_skills)}")
        else:
            st.warning("⚠️ No specific tech keywords found in this PDF.")
            
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 Cover Letter")
            if st.button("Generate Letter", key="btn_pdf_let"):
                with st.spinner("Drafting..."):
                    l = generate_application_materials(manual_title, manual_company, pdf_text, RESUME_CONTEXT)
                    st.session_state['pdf_letter'] = l
            
            if 'pdf_letter' in st.session_state:
                st.text_area("Result:", value=st.session_state['pdf_letter'], height=400)
                pdf_data = create_cover_letter_pdf(st.session_state['pdf_letter'])
                if pdf_data:
                    st.download_button(
                        label="Download Letter PDF",
                        data=pdf_data,
                        file_name=f"Michael_Morris_{safe_filename(manual_company)}_CoverLetter.pdf",
                        mime="application/pdf",
                        key="dl_pdf_let_upload"
                    )

        with col2:
            st.subheader("📄 Tailored Resume")
            if st.button("Generate Resume", key="btn_pdf_res"):
                with st.spinner("Tailoring..."):
                    r = tailor_resume(manual_title, manual_company, pdf_text, RESUME_CONTEXT)
                    st.session_state['pdf_resume'] = r
            
            if 'pdf_resume' in st.session_state:
                st.text_area("Preview:", value=st.session_state['pdf_resume'], height=300)
                pdf_data = create_pdf(st.session_state['pdf_resume'])
                if pdf_data:
                    st.download_button(
                        label="Download PDF",
                        data=pdf_data,
                        file_name=f"Michael_Morris_{safe_filename(manual_company)}_Resume.pdf",
                        mime="application/pdf",
                        key="dl_pdf_res_upload"
                    )
        
        with st.expander("View Extracted PDF Text"):
            st.write(pdf_text)

elif mode == "🔗 Direct Link Analysis":

    st.info("Paste a link from Dice or LinkedIn to instantly generate your resume/cover letter.")
    
    target_url = st.text_input("Paste Job URL here:")
    
    if st.button("Analyze Link"):
        if target_url:
            with st.spinner("Scraping job details..."):
                try:
                    job_data = asyncio.run(scrape_single_url(target_url))
                    if job_data:
                        st.session_state['current_job'] = job_data
                        st.success("Job Found!")
                    else:
                        st.error("Could not scrape that link. It might be behind a login wall.")
                except Exception as e:
                    st.error(f"Error processing link: {e}")

    if 'current_job' in st.session_state:
        job = st.session_state['current_job']
        
        # --- NEW: SKILL SCANNING ---
        found_skills = extract_keywords(job['description'])
        
        st.divider()
        st.markdown(f"## {job['title']}")
        st.caption(f"Company: {job['company']}")
        
        # --- NEW: VISUAL BADGE ---
        if found_skills:
            st.success(f"🔥 **Skills Detected:** {', '.join(found_skills)}")
        else:
            st.warning("⚠️ No specific tech keywords found in description.")
            
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 Cover Letter")
            if st.button("Generate Letter", key="btn_direct_let"):
                with st.spinner("Drafting..."):
                    l = generate_application_materials(job['title'], job['company'], job['description'], RESUME_CONTEXT)
                    st.session_state['direct_letter'] = l
            
            if 'direct_letter' in st.session_state:
                st.text_area("Result:", value=st.session_state['direct_letter'], height=400)

                # --- NEW DOWNLOAD BUTTON ---
                pdf_data = create_cover_letter_pdf(st.session_state['direct_letter'])
                if pdf_data:
                    st.download_button(
                        label="Download Letter PDF",
                        data=pdf_data,
                        file_name=f"Michael_Morris_{safe_filename(job['company'])}_CoverLetter.pdf",
                        mime="application/pdf",
                        key="dl_pdf_direct_let"
                    )
                # ---------------------------

        with col2:
            st.subheader("📄 Tailored Resume")
            if st.button("Generate Resume", key="btn_direct_res"):
                with st.spinner("Tailoring..."):
                    r = tailor_resume(job['title'], job['company'], job['description'], RESUME_CONTEXT)
                    st.session_state['direct_resume'] = r
            
            if 'direct_resume' in st.session_state:
                st.text_area("Preview:", value=st.session_state['direct_resume'], height=300)
                
                pdf_data = create_pdf(st.session_state['direct_resume'])
                clean_name = safe_filename(job['company'])
                
                if pdf_data:
                    st.download_button(
                        label="Download PDF",
                        data=pdf_data,
                        file_name=f"Michael_Morris_{clean_name}_Resume.pdf",
                        mime="application/pdf",
                        key="dl_pdf_direct"
                    )
        with st.expander("View Scraped Description"):
            st.write(job['description'])

else:
    # --- DATABASE SEARCH MODE ---
    with st.sidebar:
        st.header("Search Filters")
        num_results = st.slider("Number of jobs to retrieve", 10, 50, 30)
        
        # Scraper mode selector
        scraper_choice = st.radio(
            "Scraper Type:",
            ["📍 Local / Hybrid (NJ Area)", "🌐 Remote Help Desk (US-Wide)"],
            help="Choose which LinkedIn search to run."
        )
        if 'last_scraper' not in st.session_state:
            st.session_state['last_scraper'] = scraper_choice

    if st.button("Refresh Database (LinkedIn)"):
        with st.status("Scraping LinkedIn...", expanded=True) as status:
            st.write("Initializing browser...")
            try:
                if scraper_choice == "📍 Local / Hybrid (NJ Area)":
                    search_terms = ["Application Support", "Technical Support", "System Administrator"]
                    asyncio.run(scrape_linkedin_keywords(search_terms))
                else:
                    asyncio.run(scrape_linkedin_remote_helpdesk())
                st.session_state['last_scraper'] = scraper_choice
                status.update(label="Scrape Complete!", state="complete", expanded=False)
                st.success("Database updated! Reloading matches...")
                st.rerun()
            except Exception as e:
                st.error(f"Scraper failed: {e}")

    # Dynamic search profile based on which scraper was last used
    if st.session_state.get('last_scraper') == "🌐 Remote Help Desk (US-Wide)":
        search_profile = "Help Desk Technician, IT Support, Service Desk, Tier 1, Troubleshooting, Active Directory, Windows."
    else:
        search_profile = "Application Support Engineer, JavaScript, SQL, Troubleshooting, Linux, API."
    results = get_matches(search_profile, n_results=num_results)

    if results and results['ids'] and results['ids'][0]:
        
        # --- PRE-PROCESS & SORT BY SKILL COUNT ---
        processed_jobs = []
        for i in range(len(results['ids'][0])):
            job_desc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            
            # Count skills
            skills = extract_keywords(job_desc)
            
            processed_jobs.append({
                "index": i,
                "skills": skills,
                "skill_count": len(skills),
                "desc": job_desc,
                "meta": meta,
                "vector_score": (1 - results['distances'][0][i]) * 100
            })
        
        # SORT: Most skills first, then by vector score
        processed_jobs.sort(key=lambda x: (x['skill_count'], x['vector_score']), reverse=True)
        
        # DISPLAY RESULTS
        st.subheader(f"Top Matches based on Skill Count")
        
        # Show jobs with at least 1 skill match (help desk roles may score lower)
        min_skills = 1 if st.session_state.get('last_scraper') == "🌐 Remote Help Desk (US-Wide)" else 1
        count_shown = 0
        for job in processed_jobs:
            if job['skill_count'] < min_skills:
                continue # Skip jobs with no matching skills
            
            count_shown += 1
            job_title = job['meta'].get('title', 'Unknown Role')
            job_company = job['meta'].get('company', 'Unknown Company')
            job_url = job['meta'].get('url', '#')
            i = job['index']
            
            letter_key = f"letter_{i}"
            resume_key = f"resume_{i}"
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    if job_url != '#':
                        st.markdown(f"### 🔗 [{job_title}]({job_url})")
                    else:
                        st.markdown(f"### {job_title}")
                    st.caption(f"Company: {job_company}")
                    
                    # GREEN BADGE
                    st.success(f"🔥 **{job['skill_count']} Skills Detected:** {', '.join(job['skills'])}")
                    
                    with st.expander(f"🚀 AI Application Copilot for {job_company}"):
                        tab_letter, tab_resume = st.tabs(["📝 Cover Letter", "📄 Tailored Resume"])
                        with tab_letter:
                            if st.button(f"Draft Letter", key=f"btn_let_{i}"):
                                with st.spinner("Drafting..."):
                                    l = generate_application_materials(job_title, job_company, job['desc'], RESUME_CONTEXT)
                                    st.session_state[letter_key] = l
                            if letter_key in st.session_state:
                                st.text_area("Cover Letter:", value=st.session_state[letter_key], height=300)
                                pdf_data = create_cover_letter_pdf(st.session_state[letter_key])
                                if pdf_data:
                                    st.download_button("Download Letter PDF", pdf_data, f"CoverLetter_{safe_filename(job_company)}.pdf", "application/pdf", key=f"dl_pdf_let_{i}")

                        with tab_resume:
                            if st.button(f"Tailor Resume", key=f"btn_res_{i}"):
                                with st.spinner("Tailoring..."):
                                    r = tailor_resume(job_title, job_company, job['desc'], RESUME_CONTEXT)
                                    st.session_state[resume_key] = r
                            if resume_key in st.session_state:
                                st.text_area("Preview:", value=st.session_state[resume_key], height=200)
                                pdf_data = create_pdf(st.session_state[resume_key])
                                if pdf_data:
                                    st.download_button("Download PDF", pdf_data, f"Resume_{safe_filename(job_company)}.pdf", "application/pdf", key=f"dl_pdf_{i}")

                    with st.expander("📄 Read Full Job Description"):
                        st.write(job['desc'])
                    
                with col2:
                    st.metric("Skill Match", f"{job['skill_count']} Skills")
                    st.caption(f"Vector Score: {job['vector_score']:.1f}%")
                st.divider()
        
        if count_shown == 0:
            st.info("No jobs found with matching skills. Try checking Dice or manually adding a link.")

    else:
        st.info("No jobs found in database. Click 'Refresh Database (LinkedIn)' to start.")
