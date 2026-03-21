import os

file_path = "api/frontend.py"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1. Add Feedback Form Function after helper functions
feedback_form_func = """
def render_feedback_form(case_id, ai_response):
    \"\"\"Phase 9: Integrated Clinical Feedback Form.\"\"\"
    st.markdown(\"--- \")
    st.subheader(\"💬 Provide Feedback for Learning\")
    role = st.session_state[\"user_info\"].get(\"role\", \"patient\")
    
    with st.form(\"feedback_form_\" + str(case_id)):
        rating = st.select_slider(\"Rate this AI response (0-5)\", options=[0, 1, 2, 3, 4, 5], value=5)
        comment = st.text_area(\"Comments / ملاحظات\", placeholder=\"Tell us what to improve...\")
        
        corrected_response = None
        if role == \"doctor\":
            st.info(\"🩺 **Doctor Mode**: You can provide a clinical correction to improve the AI's medical reasoning.\")
            corrected_response = st.text_area(\"Clinical Correction (Optional)\", placeholder=\"Enter the accurate medical reasoning or diagnosis here...\")
            
        if st.form_submit_button(\"Submit Feedback\"):
            payload = {
                \"case_id\": str(case_id),
                \"rating\": rating,
                \"ai_response\": ai_response,
                \"comment\": comment,
                \"corrected_response\": corrected_response
            }
            r = api_call(\"POST\", \"/feedback/\", data=payload)
            if r and r.ok:
                st.success(\"✅ Thank you! Your feedback helps MEDAgent learn.\")
            else:
                st.error(\"Failed to submit feedback.\")

"""

# Insert after get_headers or api_call
inserted_func = False
for i, line in enumerate(lines):
    if "def api_call(method, endpoint" in line:
        # Find the end of api_call
        for j in range(i + 1, len(lines)):
            if lines[j].startswith("# ---") or lines[j].startswith("with st.sidebar:"):
                lines.insert(j, feedback_form_func)
                inserted_func = True
                break
        if inserted_func:
            break

# 2. Call feedback form in TAB 1
call_feedback = """
                # Phase 9: Feedback Integration
                if res.get("id") or res.get("report_id"):
                    render_feedback_form(res.get("report_id", "temp_case"), res.get("final_response", ""))
"""

inserted_call = False
for i, line in enumerate(lines):
    if 'st.markdown(res.get("final_response", "Waiting for plan..."))' in line:
        lines.insert(i + 1, call_feedback)
        inserted_call = True
        break

# 3. Add Feedback Analytics to TAB 13 (Analytics)
feedback_analytics_section = """
        st.divider()
        st.markdown(\"### 🧠 RLHF & System Learning\")
        if st.session_state[\"user_info\"][\"role\"] in [\"admin\", \"doctor\"]:
            if st.button(\"Refresh RLHF Analytics\"):
                r_fb = api_call(\"GET\", \"/feedback/analytics/summary\")
                if r_fb and r_fb.ok:
                    fb_data = r_fb.json()
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric(\"Avg Global Rating\", f\"{fb_data['average_rating']}/5.0\")
                    with c2: st.metric(\"Total Samples\", fb_data['total_entries'])
                    with c3: st.metric(\"Doc vs Pat\", f\"{fb_data['role_averages'].get('doctor', 0)} / {fb_data['role_averages'].get('patient', 0)}\")
                    
                    st.write(\"**Rating Distribution**\")
                    st.bar_chart(fb_data[\"rating_distribution\"])
                else:
                    st.error(\"Failed to fetch feedback analytics.\")
        else:
            st.caption(\"Detailed learning analytics are restricted to medical staff.\")
"""

inserted_analytics = False
# Tab 13 is the last tab
for i, line in enumerate(reversed(lines)):
    if 'st.caption("MEDAgent Production V5.0.0' in line:
        lines.insert(len(lines) - i - 1, feedback_analytics_section)
        inserted_analytics = True
        break

if not (inserted_func and inserted_call and inserted_analytics):
    print(
        f"Warning: Some insertions failed. Func: {inserted_func}, Call: {inserted_call}, Analytics: {inserted_analytics}"
    )

with open(file_path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("api/frontend.py updated successfully with Phase 9 UI Integration.")
