"""
MedAgent Global Medical Consultation - Web UI
Works with configurable API URL for any deployment (local, cloud, mobile backend).
"""
import os
import streamlit as st
import requests

# Configurable API base URL (any deployment)
API_BASE = os.getenv("MEDAGENT_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="MedAgent Global Medical Consultation",
    page_icon="🏥",
    layout="wide"
)

# Initialize Session State for Rating
if "last_session_id" not in st.session_state:
    st.session_state["last_session_id"] = None
if "rating_submitted" not in st.session_state:
    st.session_state["rating_submitted"] = False

st.title("🏥 MedAgent: Global Medical Consultation")
st.markdown("""
This is a **generic, global** medical support assistant. Describe your symptoms below; the system will help with 
intake, preliminary differential suggestions, and next-step guidance. **Not tied to any specific hospital or country.**
Always seek professional medical advice for diagnosis and treatment.
Support: English & Arabic 🌍
""")

# Sidebar - API status
st.sidebar.header("System Monitor")
try:
    r = requests.get(f"{API_BASE}/", timeout=5)
    api_status = r.json().get("status", "Unknown") if r.ok else "Error"
    api_ver = r.json().get("version", "")
except Exception:
    api_status = "Offline"
    api_ver = ""
st.sidebar.write(f"API Status: **{api_status}**")
st.sidebar.caption(f"Ver: {api_ver} | API: {API_BASE}")

with st.container():
    symptoms = st.text_area(
        "What symptoms are you experiencing? / ما هي الأعراض التي تشعر بها؟",
        placeholder="e.g., I have a sharp pain in my chest... / أشعر بألم في الصدر...",
        max_chars=5000
    )
    
    if st.button("Start Consultation / بدء الاستشارة"):
        st.session_state["rating_submitted"] = False
        st.session_state["last_session_id"] = None
        
        if symptoms and symptoms.strip():
            with st.spinner("Agents are processing your case... / جارِ المعالجة..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/consult",
                        json={"symptoms": symptoms.strip()},
                        timeout=180
                    )
                    if response.status_code == 200:
                        data = response.json()
                        # session_id logic if API returns it, for now assume generated
                        # In production API returns session_id in response
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.success("🤖 Patient Intake Summary")
                            st.write(data.get("summary", ""))
                            
                            st.warning("🧠 Preliminary AI Differential")
                            st.write(data.get("diagnosis", ""))
                        
                        with col2:
                            st.info("📅 Next Steps / Appointment Guidance")
                            st.write(data.get("appointment", ""))
                            
                            st.info("🩺 Clinical Note (SOAP-style)")
                            st.write(data.get("doctor_review", ""))
                        
                        # Generative Report
                        if data.get("medical_report") or data.get("doctor_summary") or data.get("patient_instructions"):
                            st.markdown("---")
                            st.subheader("📝 Generative Report (RAG)")
                            if data.get("final_response"): # Unified Response
                                st.write(data.get("final_response"))
                        
                        if data.get("is_emergency"):
                            st.error("⚠️ EMERGENCY INDICATORS DETECTED. SEEK IMMEDIATE HELP.")
                    else:
                        err = response.json().get("detail", "Unknown error")
                        st.error(f"Error: {err}")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. Please try again.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Could not connect to API: {e}")
        else:
            st.warning("Please enter your symptoms.")

# Feedback Section
st.markdown("---")
st.subheader("Rate this session (Self-Improvement)")
col_fb1, col_fb2 = st.columns([1, 4])
with col_fb1:
    rating = st.slider("Rating", 1, 5, 5)
with col_fb2:
    comment = st.text_input("Comment (Optional)")

if st.button("Submit Feedback"):
    if not st.session_state["rating_submitted"]:
         # Mock session ID for demo if API didn't return one
        sid = "demo-session" 
        try:
            requests.post(f"{API_BASE}/feedback", json={"session_id": sid, "rating": rating, "comment": comment})
            st.success("Thank you! Your feedback helps the agents learn.")
            st.session_state["rating_submitted"] = True
        except:
            st.error("Failed to submit feedback.")

st.markdown("---")
st.caption(
    "Educational & informational use only. Not a medical device. "
    "For any country, any user. Built with LangGraph, RAG, and Agentic AI."
)
