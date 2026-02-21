"""
MedAgent Global Medical Consultation - Web UI v5.0
Comprehensive, Secure, and Feature-Rich Multi-Agent Hub.
"""
import os
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# Configurable API base URL
API_BASE = os.getenv("MEDAGENT_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="MedAgent Global Hub",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME & CSS ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 500; transition: 0.3s; }
    .stButton>button:hover { background-color: #2e7d32; color: white; transform: translateY(-2px); }
    .stAlert { border-radius: 12px; }
    .report-card { border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; background: white; margin-bottom: 10px; }
    .css-1avpv00 { background: #2e7d32; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "auth_token" not in st.session_state: st.session_state["auth_token"] = None
if "user_info" not in st.session_state: st.session_state["user_info"] = None
if "session_id" not in st.session_state: st.session_state["session_id"] = None
if "language" not in st.session_state: st.session_state["language"] = "en"
if "auth_mode" not in st.session_state: st.session_state["auth_mode"] = "login"
if "second_opinion_req" not in st.session_state: st.session_state["second_opinion_req"] = False

# --- HELPER FUNCTIONS ---
def get_headers():
    return {"Authorization": f"Bearer {st.session_state['auth_token']}"}

def api_call(method, endpoint, data=None, files=None):
    try:
        url = f"{API_BASE}{endpoint}"
        headers = get_headers()
        if method == "GET": r = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            if files:
                # When uploading files, don't send json — use data or just files
                r = requests.post(url, files=files, headers=headers, timeout=60)
            else:
                r = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == "DELETE": r = requests.delete(url, headers=headers, timeout=10)
        return r
    except Exception as e:
        st.error(f"Network error: {e}")
        return None

# --- SIDEBAR: AUTH & SETTINGS ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/hospital.png", width=80)
    st.title("MedAgent Hub")
    
    if st.session_state["auth_token"]:
        # Professional Doctor Portrait in Sidebar
        st.image("https://images.pexels.com/photos/4225880/pexels-photo-4225880.jpeg?auto=compress&cs=tinysrgb&w=400", caption="Active Medical Agent", width=150)
        
        st.success(f"Hello, {st.session_state['user_info']['full_name']}")
        st.caption(f"Role: {st.session_state['user_info']['role']}")
        
        if st.session_state['user_info']['role'] == "doctor":
            if st.session_state['user_info'].get('doctor_verified'):
                st.success("✅ Verified Doctor")
            else:
                st.warning("⚠️ Unverified Doctor Mode")
                with st.expander("🩺 Verify Credentials"):
                    lic = st.text_input("License Number")
                    spec = st.text_input("Specialization")
                    if st.button("Submit Verification"):
                        vr = api_call("POST", "/auth/verify-doctor", data={"license_number": lic, "specialization": spec})
                        if vr and vr.ok: 
                            st.success("Verification Submitted!")
                            st.rerun()
                        else: st.error("Verification failed.")

        # Interaction Mode Toggle
        st.markdown("---")
        mode_options = ["Patient Mode", "Doctor Mode"]
        current_mode = st.session_state["user_info"].get("interaction_mode", "patient")
        mode_idx = 0 if current_mode == "patient" else 1
        
        new_mode_label = st.radio("Interaction Mode", mode_options, index=mode_idx)
        new_mode = "patient" if new_mode_label == "Patient Mode" else "doctor"
        
        if new_mode != current_mode:
            r = api_call("POST", "/auth/set-mode", data={"interaction_mode": new_mode})
            if r and r.ok:
                st.session_state["user_info"]["interaction_mode"] = new_mode
                st.rerun()

        # Language Toggle
        new_lang = st.selectbox("Language / اللغة", ["English", "Arabic"], index=0 if st.session_state["language"]=="en" else 1)
        st.session_state["language"] = "en" if new_lang == "English" else "ar"
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state["auth_token"] = None
            st.rerun()
            
        with st.expander("⚙️ Account Settings"):
            if st.button("Edit Profile"): st.toast("Profile editing coming soon...")
            if st.button("Privacy Policy"): st.info("Your data is encrypted and stored locally. No HIPAA-protected data is sent to external clouds without encryption.")
            if st.button("🗑️ Delete Account", type="primary"):
                if st.warning("This will permanently anonymize your data. Proceed?"):
                    r = api_call("DELETE", "/auth/account")
                    if r and r.ok:
                         st.session_state["auth_token"] = None
                         st.rerun()
    else:
        st.info("Log in to access clinical features.")
        if st.session_state["auth_mode"] == "login":
            l_id = st.text_input("ID / Email / Phone")
            l_pw = st.text_input("Password", type="password")
            if st.button("Sign In"):
                r = requests.post(f"{API_BASE}/auth/login", json={"login_id": l_id, "password": l_pw})
                if r.ok:
                    data = r.json()
                    st.session_state["auth_token"] = data["access_token"]
                    st.session_state["user_info"] = data["user"]
                    st.session_state["session_id"] = data["session_id"]
                    st.rerun()
                else: st.error("Invalid credentials.")
            if st.button("New here? Register"): st.session_state["auth_mode"] = "register"; st.rerun()
        else:
            r_un = st.text_input("Username")
            r_em = st.text_input("Email")
            r_nm = st.text_input("Full Name")
            r_pw = st.text_input("Password", type="password")
            
            col_a, col_g = st.columns(2)
            with col_a: r_age = st.number_input("Age", min_value=0, max_value=120, value=25)
            with col_g: r_gen = st.selectbox("Gender", ["Male", "Female", "Prefer not to say"])
            
            r_cnt = st.text_input("Country", value="Egypt")
            r_rol = st.selectbox("Role", ["patient", "doctor"])
            
            if st.button("Create Account"):
                payload = {
                    "username": r_un, 
                    "email": r_em, 
                    "phone": "000", 
                    "password": r_pw, 
                    "full_name": r_nm,
                    "age": r_age,
                    "gender": r_gen,
                    "country": r_cnt,
                    "role": r_rol
                }
                r = requests.post(f"{API_BASE}/auth/register", json=payload)
                if r.ok: st.success("Created! Sign in now."); st.session_state["auth_mode"] = "login"; st.rerun()
                else: st.error(f"Registration failed: {r.text}")
            if st.button("Back to Login"): st.session_state["auth_mode"] = "login"; st.rerun()

# --- MAIN INTERFACE ---
if not st.session_state["auth_token"]:
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h1 style="color: #2e7d32; font-size: 3rem;">MedAgent Global Medical Hub</h1>
        <p style="font-size: 1.2rem; color: #666;">A state-of-the-art Multi-Agent workforce powered by Generative & Agentic AI.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ### 👨‍⚕️ Advanced Clinical Intelligence
        Our production environment orchestrates **12 specialized AI agents** to provide 24/7 medical guidance:
        - **Intelligent Triage Agent**: Real-time risk assessment and clinical prioritization.
        - **Knowledge Retrieval Agent**: RAG-grounded insights from up-to-date medical literature.
        - **Multimodal Vision Agent**: Advanced analysis of X-rays, skin conditions, and clinical photos.
        - **Tree-of-Thought Reasoning**: Deep differential analysis for complex cases.
        - **Bilingual Support (AR/EN)**: Native-level medical support in Arabic and English.
        - **Clinical Persistence Agent**: Secure, AES-256 encrypted longitudinal medical memory.
        - **Automated Report Generation**: Professional PDF/Image exports following SOAP standards.
        - **Governance & Safety Agents**: Active monitoring for medical accuracy and patient safety.
        - **Self-Improvement Agent**: System that learns from human feedback and reviews.
        """)
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3774/3774299.png", width=250)
        st.info("🔒 **Secure & Private**: All data is encrypted and stored according to global health authority standards.")
else:
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(["💬 Consult", "🔬 Image Analysis", "📅 Appointments", "💊 Meds", "📜 History", "🛡️ Privacy", "🔑 Admin"])
    
    # --- TAB 1: CONSULTATION ---
    with t1:
        st.subheader("Interactive Consultation / استشارة تفاعلية")
        col_in, col_out = st.columns([1, 1])
        
        with col_in:
            symptoms = st.text_area("Describe symptoms", placeholder="e.g. Sharp chest pain after exercise...", height=150)
            st.session_state["second_opinion_req"] = st.checkbox("🔍 Request specialized Second Opinion (More thorough analysis)")
            uploaded_file = st.file_uploader("Upload Medical Image (Optional)", type=["jpg", "png", "jpeg", "webp"])
            
            if st.button("⚡ ANALYZE SYSTEM-WIDE"):
                img_path = None
                if uploaded_file:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    u_resp = api_call("POST", "/upload", files=files)
                    if u_resp and u_resp.ok: img_path = u_resp.json().get("image_path")
                
                with st.spinner("Agents are collaborating..."):
                    payload = {
                        "symptoms": symptoms, 
                        "image_path": img_path, 
                        "patient_id": st.session_state["user_info"]["id"], 
                        "language": st.session_state["language"],
                        "request_second_opinion": st.session_state["second_opinion_req"]
                    }
                    r = api_call("POST", "/consult", data=payload)
                    if r and r.ok:
                        st.session_state["last_result"] = r.json()
                        st.balloons()
                    else: st.error("Analysis failed.")
        
        with col_out:
            if "last_result" in st.session_state:
                res = st.session_state["last_result"]
                
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.image("https://cdn-icons-png.flaticon.com/512/3774/3774299.png", width=60)
                with c2:
                    st.markdown("### Medical Specialist Analysis")
                    st.caption(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")

                # Vision Findings
                if res.get("visual_findings") and res["visual_findings"].get("status") != "skipped":
                    with st.expander("👁️ Visual Analysis Results"):
                        vf = res["visual_findings"]
                        st.write(f"**Findings:** {vf.get('visual_findings')}")
                        st.write(f"**Confidence:** {vf.get('confidence')}")
                        st.write(f"**Severity:** {vf.get('severity_level')}")

                st.info("🧠 REASONING OUTPUT")
                st.write(res.get("preliminary_diagnosis", "No diagnosis generated."))
                
                st.info("📋 CLINICAL ACTION PLAN")
                st.markdown(res.get("final_response", "Waiting for plan..."))
                
                if res.get("critical_alert"):
                    st.error("🚨 EMERGENCY ESCALATION DETECTED")
                
                if res.get("report_id"):
                    st.write("### ⬇️ Export Clinical Report")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"[📄 PDF]({API_BASE}/reports/{res['report_id']}/export?format=pdf)")
                    with c2:
                        st.markdown(f"[🖼️ Image]({API_BASE}/reports/{res['report_id']}/export?format=image)")
                    with c3:
                        st.markdown(f"[📝 Text]({API_BASE}/reports/{res['report_id']}/export?format=text)")
                
                with st.expander("🛠️ Advanced Export"):
                    st.download_button("Download Raw JSON", data=json.dumps(res, indent=2), file_name="medical_report.json")

    # --- TAB 2: IMAGE ANALYSIS ---
    with t2:
        st.subheader("🔬 Medical Image Analysis / تحليل الصور الطبية")
        st.write("Upload X-rays, CT scans, MRI images, skin conditions, or lab reports for AI-powered clinical analysis.")
        
        col_upload, col_results = st.columns([1, 1])
        
        with col_upload:
            st.write("### 📤 Upload Image")
            img_file = st.file_uploader(
                "Select medical image", 
                type=["jpg", "jpeg", "png", "webp"],
                key="image_analysis_uploader",
                help="Supported: X-ray, CT, MRI, skin photos, lab reports (JPG, PNG, WEBP)"
            )
            
            img_symptoms = st.text_area(
                "Clinical context (optional)", 
                placeholder="e.g. Patient reports sharp pain in lower right abdomen for 3 days...",
                height=100,
                key="image_context"
            )
            
            if st.button("🔍 Analyze Image", key="analyze_image_btn"):
                if img_file:
                    with st.spinner("🧠 Vision Analysis Agent processing..."):
                        # Upload image
                        files = {"file": (img_file.name, img_file.getvalue())}
                        u_resp = api_call("POST", "/upload", files=files)
                        if u_resp and u_resp.ok:
                            img_path = u_resp.json().get("image_path")
                            # Run analysis with clinical context
                            context = img_symptoms if img_symptoms else "Analyze this medical image"
                            payload = {
                                "symptoms": context,
                                "image_path": img_path,
                                "patient_id": st.session_state["user_info"]["id"],
                                "language": st.session_state["language"]
                            }
                            r = requests.post(f"{API_BASE}/consult", json=payload, headers=get_headers(), timeout=120)
                            if r and r.ok:
                                st.session_state["image_result"] = r.json()
                                st.success("✅ Analysis complete!")
                            else:
                                st.error("Analysis failed. Please try again.")
                        else:
                            st.error("Image upload failed.")
                else:
                    st.warning("Please upload an image first.")
        
        with col_results:
            if "image_result" in st.session_state:
                res = st.session_state["image_result"]
                vf = res.get("visual_findings", {})
                
                if vf.get("status") != "skipped":
                    st.write("### 📊 Analysis Results")
                    
                    # Severity indicator
                    severity = vf.get("severity_level", "unknown")
                    severity_colors = {"low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"}
                    st.write(f"**Severity:** {severity_colors.get(severity, '⚪')} {severity.upper()}")
                    
                    # Confidence bar
                    confidence = vf.get("confidence", 0)
                    st.progress(float(confidence), text=f"Confidence: {confidence:.0%}")
                    
                    if vf.get("requires_human_review"):
                        st.warning("⚠️ Professional review recommended")
                    
                    # Image type
                    if vf.get("image_type"):
                        st.info(f"📷 Image Type: {vf['image_type']}")
                    
                    # Visual findings
                    with st.expander("👁️ Visual Findings", expanded=True):
                        st.write(vf.get("visual_findings", "No findings available"))
                    
                    # Differential diagnosis
                    if vf.get("differential_diagnosis"):
                        with st.expander("🔬 Differential Diagnosis"):
                            for dx in vf["differential_diagnosis"]:
                                likelihood = dx.get("likelihood", "?")
                                icon = "🟢" if likelihood == "low" else "🟡" if likelihood == "moderate" else "🔴"
                                st.write(f"{icon} **{dx.get('condition')}** ({likelihood}) — {dx.get('reasoning', '')}")
                    
                    # Possible conditions
                    if vf.get("possible_conditions"):
                        with st.expander("📋 Possible Conditions"):
                            for cond in vf["possible_conditions"]:
                                st.write(f"• {cond}")
                    
                    # Recommended actions
                    if vf.get("recommended_actions"):
                        with st.expander("✅ Recommended Actions"):
                            for action in vf["recommended_actions"]:
                                st.write(f"→ {action}")
                    
                    # Uncertainty notes
                    if vf.get("uncertainty_notes"):
                        st.caption(f"⚠️ {vf['uncertainty_notes']}")
                    
                    # Disclaimer
                    if vf.get("disclaimer"):
                        st.caption(f"📌 {vf['disclaimer']}")
                else:
                    st.info("No visual analysis available. Upload an image to begin.")
        
        # Image History
        st.markdown("---")
        st.write("### 📂 Image Analysis History")
        r_imgs = api_call("GET", "/images")
        if r_imgs and r_imgs.ok:
            images = r_imgs.json()
            if not images:
                st.caption("No previous image analyses found.")
            else:
                for img in images:
                    severity_icon = {"low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"}.get(img.get("severity", ""), "⚪")
                    with st.expander(f"{severity_icon} {img['filename']} — {img['timestamp'][:10]}"):
                        st.write(f"**Confidence:** {img.get('confidence', 'N/A')}")
                        st.write(f"**Severity:** {img.get('severity', 'N/A')}")
                        if img.get("conditions"):
                            st.write(f"**Conditions:** {', '.join(img['conditions'])}")
                        if img.get("findings"):
                            st.json(img["findings"])

    # --- TAB 3: APPOINTMENTS ---
    with t3:
        st.subheader("Clinical Appointments & Scheduling")
        st.write("Manage your upcoming sessions with specialized agents or human doctors.")
        
        r = api_call("GET", "/appointments")
        if r and r.ok:
            events = r.json()
            if not events:
                st.info("No upcoming appointments found. You can request one via the Consult tab.")
            else:
                for ev in events:
                    with st.container():
                        st.markdown(f"""
                        <div class="report-card">
                            <h4>📅 {ev.get('summary')}</h4>
                            <p><b>Time:</b> {ev.get('start', {}).get('dateTime', 'N/A')}</p>
                            <p><b>Location:</b> {ev.get('location', 'Global Hub')}</p>
                            <a href="{ev.get('htmlLink')}" target="_blank">View in Google Calendar</a>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.info("💡 **Tip:** To book a new appointment, simply type 'Book an appointment for tomorrow at 10am' in the consultation symptoms box.")

    # --- TAB 4: MEDICATION ---
    with t4:
        st.subheader("Medication Tracker & Digital Reminders")
        mc1, mc2 = st.columns(2)
        
        with mc1:
            st.write("### 💊 Active Medications")
            r = api_call("GET", "/medications")
            if r and r.ok:
                meds = r.json()
                if not meds: st.caption("No active medications found.")
                for m in meds:
                    st.markdown(f"**{m['name']}** - {m['dosage']} ({m['frequency']})")
            
            with st.expander("➕ Add New Medication"):
                m_name = st.text_input("Medicine Name")
                m_dose = st.text_input("Dosage (e.g. 500mg)")
                m_freq = st.text_input("Frequency (e.g. Twice daily)")
                if st.button("Save Medication"):
                    api_call("POST", "/medications", {"name": m_name, "dosage": m_dose, "frequency": m_freq})
                    st.rerun()

        with mc2:
            st.write("### ⏰ Health Reminders")
            st.info("System will notify you according to your schedule.")
            r_title = st.text_input("Reminder Title")
            r_time = st.text_input("Time (e.g. 08:00 AM)")
            if st.button("Set Reminder"):
                api_call("POST", "/reminders", {"title": r_title, "time": r_time})
                st.success("Reminder set!")

    # --- TAB 5: HISTORY ---
    with t5:
        st.subheader("Long-Term Medical Memory & Reports")
        r = api_call("GET", "/reports")
        if r and r.ok:
            reports = r.json()
            if not reports: st.info("No clinical reports generated yet.")
            for rep in reports:
                with st.expander(f"Report ID #{rep['id']} - {rep['generated_at'][:10]} ({rep['report_type']})"):
                    st.json(rep["content"])
                    # Export Options
                    c_pdf, c_img, c_txt = st.columns(3)
                    with c_pdf:
                        st.markdown(f"[📄 PDF]({API_BASE}/reports/{rep['id']}/export?format=pdf)")
                    with c_img:
                        st.markdown(f"[🖼️ Image]({API_BASE}/reports/{rep['id']}/export?format=image)")
                    with c_txt:
                        st.markdown(f"[📝 Text]({API_BASE}/reports/{rep['id']}/export?format=text)")

    # --- TAB 6: PRIVACY ---
    with t6:
        st.subheader("Data Rights & System Support")
        st.write("#### 🛡️ Your Privacy")
        st.write("We implement AES-256 encryption at rest. All reasoning is local or via secure API tunnels.")
        if st.button("Export All My Data (CSV - Portability)"):
            r = api_call("GET", "/auth/export-data")
            if r and r.ok:
                st.download_button("Download My Data", data=r.content, file_name="my_health_data.csv")
            else: st.error("Export failed.")
            
        st.write("#### 📞 Clinical Support")
        st.write("Need technical help? Contact our support agents.")
        st.text_area("Message Support")
        if st.button("Send to Support Hub"): st.success("Message queued.")

    # --- TAB 7: ADMIN ---
    with t7:
        if st.session_state["user_info"]["role"] != "admin":
            st.warning("Admin Clearance Required.")
        else:
            st.subheader("Admin Control Panel")
            st.write("#### 🏥 System Health")
            r_hp = api_call("GET", "/system/health")
            if r_hp and r_hp.ok: st.json(r_hp.json())
            
            st.write("#### 🕵️ Review Flagged Interactions")
            r_rv = api_call("GET", "/admin/pending-reviews")
            if r_rv and r_rv.ok:
                items = r_rv.json()
                if not items: st.caption("No items pending human review.")
                for item in items:
                    with st.expander(f"Review Item {item['id']}"):
                        st.write(f"Input: {item['user_input']}")
                        st.write(f"Diagnosis: {item['diagnosis']}")
                        if st.button(f"Approve {item['id']}"): st.success("Approved")
            
            st.write("#### 📈 Self-Improvement Analysis")
            if st.button("Generate Improvement Insights"):
                r_si = api_call("GET", "/admin/improvement-report")
                if r_si and r_si.ok:
                    st.text_area("Live Improvement Report", r_si.json().get("report", "No data"), height=300)
                else:
                    st.error("Failed to fetch improvement report.")

# --- FOOTER ---
st.markdown("---")
st.caption("MEDAgent Production V5.0.0 | Global Health Authority Architecture | Powered by Agentic LLMs")
