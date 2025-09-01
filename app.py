import io
from typing import Dict, Any, List
import streamlit as st
import pandas as pd
import altair as alt
from streamlit.components.v1 import html as stc_html

import backend

# Page config
st.set_page_config(page_title="Advanced Student Performance Tracker", page_icon="🎓", layout="wide")

# Global styles
CUSTOM_CSS = """
<style>
    /* App wrapper: remove extra top padding completely */
    .app-bg {
        background: transparent !important;
        min-height: 100vh;
        padding: 0 0 1.25rem 0; /* was 0.5rem top; remove to avoid initial scroll */
    }

    /* Hide Streamlit header/toolbar entirely */
    [data-testid="stHeader"] { 
        height: 0 !important; 
        min-height: 0 !important; 
        background: transparent !important; 
        display: none !important;
    }
    [data-testid="stToolbar"] { display: none !important; }

    /* Remove ALL top padding/margin on main block container */
    [data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; }
    [data-testid="stAppViewContainer"] > .main .block-container {
        padding-top: 0 !important;         /* was 0.5rem */
        margin-top: 0 !important;
        padding-bottom: 1.25rem !important;
    }
    /* Ensure very first element starts at the absolute top */
    [data-testid="stAppViewContainer"] .block-container > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* Prevent an empty first vertical block from reserving height */
    [data-testid="stAppViewContainer"] .block-container > [data-testid="stVerticalBlock"]:first-of-type > div:empty {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Section wrapper transparent and no shadow/border/radius */
    .card {
        max-width: 720px;
        margin: 0 auto;
        background: transparent !important;
        backdrop-filter: none !important;
        border: 0 !important;
        border-radius: 0 !important;
        padding: 24px 24px 16px 24px;
        box-shadow: none !important;
    }

    /* Hard-kill any default block/container backgrounds */
    [data-testid="stAppViewContainer"],
    section.main,
    [data-testid="stSidebar"],
    [data-testid="stVerticalBlock"] > div,
    [data-testid="stHorizontalBlock"] > div,
    [data-testid="stBlock"] > div,
    [data-testid="stExpander"] > div {
        background: transparent !important;
        box-shadow: none !important;
        border: 0 !important;
    }

    /* Charts and images transparent */
    [data-testid="stVegaLiteChart"],
    [data-testid="stVegaLiteChart"] canvas,
    .vega-embed,
    [data-testid="stImage"],
    .stImage img {
        background: transparent !important;
        box-shadow: none !important;
        border: 0 !important;
    }

    .center { display: flex; align-items: center; justify-content: center; }
    .muted { color: #5f6368; }
    .header-title { margin-bottom: 0.25rem; line-height: 1.2; }
    .stButton>button {
        background: #2563eb !important;
        color: #fff !important;
        border: none;
        padding: 0.6rem 1rem;
        border-radius: 10px;
    }
    .stDownloadButton>button {
        background: #059669 !important;
        color: #fff !important;
        border: none;
        padding: 0.6rem 1rem;
        border-radius: 10px;
    }
    .danger>button { background: #dc2626 !important; }
    .neutral>button { background: #6b7280 !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <style>
      /* Ensure no top padding on main container */
      [data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; }
      [data-testid="stAppViewContainer"] .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
      }
      /* Collapse any tall first block that keeps height even when transparent */
      [data-testid="stAppViewContainer"] .block-container > [data-testid="stVerticalBlock"]:first-of-type {
        margin-top: 0 !important;
        padding-top: 0 !important;
        min-height: 0 !important;
        height: auto !important;
      }
      /* Remove default top margin on the first heading so it sticks to the top */
      [data-testid="stAppViewContainer"] .block-container h1:first-child,
      [data-testid="stAppViewContainer"] .block-container h2:first-child,
      [data-testid="stAppViewContainer"] .block-container h3:first-child {
        margin-top: 0 !important;
      }
      /* If a placeholder image/chart sits in the very first block, hide it */
      [data-testid="stAppViewContainer"] .block-container > [data-testid="stVerticalBlock"]:first-of-type [data-testid="stImage"]:first-of-type,
      [data-testid="stAppViewContainer"] .block-container > [data-testid="stVerticalBlock"]:first-of-type [data-testid="stVegaLiteChart"]:first-of-type {
        display: none !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

stc_html(
    "<script>window.requestAnimationFrame(()=>window.scrollTo(0,0));</script>",
    height=0
)

st.markdown('<div class="app-bg">', unsafe_allow_html=True)

# Session state
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "username": "", "role": ""}


def logout():
    st.session_state.auth = {"logged_in": False, "username": "", "role": ""}


with st.sidebar:
    st.title("🎓 Tracker")
    if st.session_state.auth["logged_in"]:
        st.write(f"Signed in as: {st.session_state.auth['username']} ({st.session_state.auth['role']})")
        st.button("Logout", on_click=logout, key="logout_btn")
    else:
        st.write("Please login or register.")

def welcome_card():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("Welcome!", anchor=False)
    st.write("Please select Student or Teacher login / Register.")

    tabs = st.tabs(["Login", "Register"])

    with tabs[0]:
        role = st.selectbox("Role", ["Student", "Teacher"], key="login_role")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", type="primary", use_container_width=True, key="login_button"):
            ok, user_role, msg = backend.login_user(username, password)
            if ok and user_role == role:
                st.session_state.auth = {"logged_in": True, "username": username, "role": user_role}
                st.success("Login successful.")
                st.rerun()
            elif ok and user_role != role:
                st.error(f"Role mismatch: your account role is {user_role}.")
            else:
                st.error(msg)

    with tabs[1]:
        role_r = st.selectbox("Register as", ["Student", "Teacher"], key="register_role")
        username_r = st.text_input("Username", key="register_username")
        password_r = st.text_input("Password", type="password", key="register_password")
        if st.button("Register", use_container_width=True, key="register_button"):
            ok, msg = backend.register_user(username_r, password_r, role_r)
            if ok:
                st.success("Registration successful. You can login now.")
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)


def student_dashboard():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Student Dashboard", anchor=False)
    st.caption("Enter your performance data to get a predicted grade and recommendations.")

    with st.form("student_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            attendance = st.number_input("Attendance (%)", min_value=0.0, max_value=100.0, value=85.0, step=1.0)
            marks = st.number_input("Marks (%)", min_value=0.0, max_value=100.0, value=78.0, step=1.0)
            assignments = st.number_input("Assignments (%)", min_value=0.0, max_value=100.0, value=80.0, step=1.0)
        with col2:
            study_hours = st.number_input("Study Hours per week", min_value=0.0, max_value=80.0, value=12.0, step=1.0)
            extracurriculars = st.number_input("Extracurricular activities (0–10)", min_value=0.0, max_value=10.0, value=3.0, step=1.0)
        submitted = st.form_submit_button("Predict Grade", use_container_width=True)

    if submitted:
        data = {
            "attendance": attendance,
            "marks": marks,
            "assignments": assignments,
            "study_hours": study_hours,
            "extracurriculars": extracurriculars,
        }
        grade, prob_map = backend.predict_grade(data)
        st.success(f"Predicted Grade: {grade}")

        # Probabilities bar chart using Altair
        prob_df = pd.DataFrame({
            "Grade": list(prob_map.keys()),
            "Probability": [round(p, 4) for p in prob_map.values()],
        })
        grade_order = ["A", "B", "C", "D"]
        prob_df["Grade"] = pd.Categorical(prob_df["Grade"], categories=grade_order, ordered=True)
        prob_df = prob_df.sort_values("Grade")

        prob_chart = (
            alt.Chart(prob_df)
            .mark_bar(cornerRadius=4)
            .encode(
                y=alt.Y("Grade:N", sort=grade_order, title="Grade", axis=alt.Axis(labelAngle=0)),
                x=alt.X("Probability:Q", title="Probability", axis=alt.Axis(format="%")),
                color=alt.Color("Grade:N", legend=None),
                tooltip=[alt.Tooltip("Grade:N"), alt.Tooltip("Probability:Q", format=".1%")],
            )
            .properties(height=160, width="container")
            .configure_view(strokeWidth=0)
            .configure(background="transparent")
        )
        st.altair_chart(prob_chart, use_container_width=True, theme=None)

        risk_score, risk_level, risk_actions = backend.compute_risk(data, prob_map)
        st.markdown("##### Risk assessment")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Risk level", risk_level)
        with c2:
            st.progress(risk_score, text=f"{int(risk_score * 100)}%")

        st.markdown("###### How to reduce risk")
        for tip in risk_actions:
            st.write(f"- {tip}")

        # Recommendations
        recs = backend.get_recommendations(data)
        st.markdown("##### Recommendations")
        for r in recs:
            st.write(f"- {r}")

        # Save record (use username as the student's 'name')
        name = st.session_state.auth["username"]
        record_id = backend.add_student(
            name=name,
            attendance=attendance,
            marks=marks,
            assignments=assignments,
            study_hours=study_hours,
            extracurriculars=extracurriculars,
            predicted_grade=grade,
        )

        # Download CSV
        csv_df = pd.DataFrame([{
            "id": record_id,
            "name": name,
            "attendance": attendance,
            "marks": marks,
            "assignments": assignments,
            "study_hours": study_hours,
            "extracurriculars": extracurriculars,
            "predicted_grade": grade,
        }])
        csv_bytes = csv_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download report (CSV)",
            data=csv_bytes,
            file_name=f"{name}_report_{record_id}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Download PDF
        pdf_bytes = generate_pdf(
            name=name,
            record_id=record_id,
            data=data,
            grade=grade,
            recommendations=recs,
        )
        st.download_button(
            label="Download report (PDF)",
            data=pdf_bytes,
            file_name=f"{name}_report_{record_id}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # History
    with st.expander("View my recent submissions"):
        rows = backend.get_students_by_name(st.session_state.auth["username"])
        if rows:
            st.dataframe(pd.DataFrame(rows))
        else:
            st.info("No submissions yet.")

    st.markdown("</div>", unsafe_allow_html=True)


def teacher_dashboard():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Teacher Dashboard", anchor=False)
    st.caption("Manage student records and see class-level insights.")

    tab_view, tab_add, tab_update, tab_remove, tab_reports = st.tabs(
        ["View Records", "Add Record", "Update Record", "Remove Record", "Reports"]
    )

    with tab_view:
        rows = backend.get_all_students()
        if rows:
            st.dataframe(pd.DataFrame(rows))
        else:
            st.info("No records yet.")

    with tab_add:
        st.markdown("##### Add new student record")
        with st.form("add_student_form"):
            name = st.text_input("Student Name")
            c1, c2 = st.columns(2)
            with c1:
                attendance = st.number_input("Attendance (%)", 0.0, 100.0, 90.0, 1.0, key="t_add_att")
                marks = st.number_input("Marks (%)", 0.0, 100.0, 85.0, 1.0, key="t_add_marks")
                assignments = st.number_input("Assignments (%)", 0.0, 100.0, 80.0, 1.0, key="t_add_asg")
            with c2:
                study_hours = st.number_input("Study Hours per week", 0.0, 80.0, 10.0, 1.0, key="t_add_study")
                extracurriculars = st.number_input("Extracurricular (0–10)", 0.0, 10.0, 2.0, 1.0, key="t_add_extra")
            submitted = st.form_submit_button("Add", use_container_width=True)
        if submitted:
            if not name:
                st.error("Name is required.")
            else:
                grade, _ = backend.predict_grade(
                    {
                        "attendance": attendance,
                        "marks": marks,
                        "assignments": assignments,
                        "study_hours": study_hours,
                        "extracurriculars": extracurriculars,
                    }
                )
                sid = backend.add_student(
                    name, attendance, marks, assignments, study_hours, extracurriculars, grade
                )
                st.success(f"Added record for {name} (ID {sid})")

    with tab_update:
        rows = backend.get_all_students()
        if not rows:
            st.info("No records to update.")
        else:
            df = pd.DataFrame(rows)
            ids = df["id"].tolist()
            selected_id = st.selectbox("Select record ID to update", ids)
            record = df[df["id"] == selected_id].iloc[0].to_dict()

            with st.form("update_student_form"):
                name = st.text_input("Student Name", value=str(record["name"]))
                c1, c2 = st.columns(2)
                with c1:
                    attendance = st.number_input("Attendance (%)", 0.0, 100.0, float(record["attendance"]), 1.0, key="t_upd_att")
                    marks = st.number_input("Marks (%)", 0.0, 100.0, float(record["marks"]), 1.0, key="t_upd_marks")
                    assignments = st.number_input("Assignments (%)", 0.0, 100.0, float(record["assignments"]), 1.0, key="t_upd_asg")
                with c2:
                    study_hours = st.number_input("Study Hours per week", 0.0, 80.0, float(record["study_hours"]), 1.0, key="t_upd_study")
                    extracurriculars = st.number_input("Extracurricular (0–10)", 0.0, 10.0, float(record["extracurriculars"]), 1.0, key="t_upd_extra")
                update_btn = st.form_submit_button("Update", use_container_width=True)

            if update_btn:
                # Recalculate grade using ML
                grade, _ = backend.predict_grade(
                    {
                        "attendance": attendance,
                        "marks": marks,
                        "assignments": assignments,
                        "study_hours": study_hours,
                        "extracurriculars": extracurriculars,
                    }
                )
                ok = backend.update_student(
                    int(selected_id),
                    name,
                    attendance,
                    marks,
                    assignments,
                    study_hours,
                    extracurriculars,
                    grade,
                )
                if ok:
                    st.success(f"Record {selected_id} updated. New grade: {grade}")
                else:
                    st.error("Update failed.")

    with tab_remove:
        rows = backend.get_all_students()
        if not rows:
            st.info("No records to remove.")
        else:
            df = pd.DataFrame(rows)
            ids = df["id"].tolist()
            selected_id = st.selectbox("Select record ID to remove", ids, key="remove_id")
            if st.button("Remove", use_container_width=True, key="remove_btn"):
                ok = backend.remove_student(int(selected_id))
                if ok:
                    st.success(f"Removed record {selected_id}")
                else:
                    st.error("Remove failed.")

    with tab_reports:
        rows = backend.get_all_students()
        if not rows:
            st.info("No data for reports yet.")
        else:
            df = pd.DataFrame(rows)
            st.markdown("##### Grade Distribution")
            grade_counts = df["predicted_grade"].value_counts()
            grade_order = ["A", "B", "C", "D"]
            grade_counts = grade_counts.reindex(grade_order).fillna(0).astype(int).reset_index()
            grade_counts.columns = ["Grade", "Count"]

            grade_chart = (
                alt.Chart(grade_counts)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X("Grade:N", sort=grade_order, title="Grade", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Count:Q", title="Count"),
                    color=alt.Color("Grade:N", legend=None),
                    tooltip=["Grade", "Count"],
                )
                .properties(height=220, width="container")
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )
            st.altair_chart(grade_chart, use_container_width=True, theme=None)

            st.markdown("##### Risk Overview")
            def _row_risk(row):
                data = {
                    "attendance": float(row["attendance"]),
                    "marks": float(row["marks"]),
                    "assignments": float(row["assignments"]),
                    "study_hours": float(row["study_hours"]),
                    "extracurriculars": float(row["extracurriculars"]),
                }
                pseudo_probs = {"A": 0, "B": 0, "C": 0, "D": 0}
                pseudo_probs[str(row["predicted_grade"])] = 1.0
                score, level, _ = backend.compute_risk(data, pseudo_probs)
                return score, level

            df["risk_score"], df["risk_level"] = zip(*df.apply(_row_risk, axis=1))
            risk_counts = df["risk_level"].value_counts().reindex(["High", "Medium", "Low"]).fillna(0).astype(int).reset_index()
            risk_counts.columns = ["Risk", "Count"]

            risk_chart = (
                alt.Chart(risk_counts)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X("Risk:N", sort=["High", "Medium", "Low"], title="Risk Level", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Count:Q", title="Students"),
                    color=alt.Color("Risk:N", scale=alt.Scale(domain=["High", "Medium", "Low"], range=["#dc2626", "#f59e0b", "#16a34a"]), legend=None),
                    tooltip=["Risk", "Count"],
                )
                .properties(height=220, width="container")
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )
            st.altair_chart(risk_chart, use_container_width=True, theme=None)

            st.markdown("##### Attendance vs Marks (by Risk)")
            scatter = (
                alt.Chart(df)
                .mark_circle(opacity=0.8)
                .encode(
                    x=alt.X("attendance:Q", title="Attendance (%)"),
                    y=alt.Y("marks:Q", title="Marks (%)"),
                    size=alt.Size("assignments:Q", title="Assignments (%)", legend=None),
                    color=alt.Color("risk_level:N", title="Risk", scale=alt.Scale(domain=["High", "Medium", "Low"], range=["#dc2626", "#f59e0b", "#16a34a"])),
                    tooltip=["name", "attendance", "marks", "assignments", "study_hours", "extracurriculars", "predicted_grade", alt.Tooltip("risk_score:Q", format=".0%")],
                )
                .properties(height=280, width="container")
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )
            st.altair_chart(scatter, use_container_width=True, theme=None)

            st.markdown("##### Marks by Grade (Box Plot)")
            box = (
                alt.Chart(df)
                .mark_boxplot(size=40)
                .encode(
                    x=alt.X("predicted_grade:N", sort=grade_order, title="Grade", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("marks:Q", title="Marks (%)"),
                    color=alt.Color("predicted_grade:N", legend=None),
                )
                .properties(height=240, width="container")
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )
            st.altair_chart(box, use_container_width=True, theme=None)

            st.markdown("##### Attendance × Assignments — Avg Marks (Heatmap)")
            heatmap = (
                alt.Chart(df)
                .mark_rect()
                .encode(
                    x=alt.X("attendance:Q", bin=alt.Bin(maxbins=10), title="Attendance (%)"),
                    y=alt.Y("assignments:Q", bin=alt.Bin(maxbins=10), title="Assignments (%)"),
                    color=alt.Color("mean(marks):Q", title="Avg Marks", scale=alt.Scale(scheme="blues")),
                    tooltip=[alt.Tooltip("count():Q", title="Students"), alt.Tooltip("mean(marks):Q", title="Avg Marks", format=".1f")],
                )
                .properties(height=260, width="container")
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )
            st.altair_chart(heatmap, use_container_width=True, theme=None)

            with st.expander("Risk Mitigation Guide"):
                st.markdown(
                    "- High risk: prioritize attendance contracts, daily study blocks, and early assignment drafts with feedback.\n"
                    "- Medium risk: weekly progress reviews, targeted tutoring on weak topics, and 12–15 hrs/week study plan.\n"
                    "- Low risk: maintain habits; set monthly goals and peer study groups to keep momentum."
                )

            # Existing average metrics table
            st.markdown("##### Average Metrics")
            avg_df = df[
                ["attendance", "marks", "assignments", "study_hours", "extracurriculars"]
            ].mean().round(2)
            st.dataframe(avg_df.to_frame(name="Average"))

            st.markdown("##### Top At-Risk Students")
            top_at_risk = df.sort_values("risk_score", ascending=False).loc[df["risk_level"] == "High", ["id", "name", "attendance", "marks", "assignments", "study_hours", "extracurriculars", "predicted_grade", "risk_score"]].copy()
            top_at_risk["risk_score"] = (top_at_risk["risk_score"] * 100).round(0).astype(int).astype(str) + "%"
            if len(top_at_risk):
                st.dataframe(top_at_risk.reset_index(drop=True))
            else:
                st.info("No students currently flagged as High risk.")

    st.markdown("</div>", unsafe_allow_html=True)


def generate_pdf(name: str, record_id: int, data: Dict[str, Any], grade: str, recommendations: List[str]) -> bytes:
    # Generates a simple PDF using reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
    except Exception:
        # Fallback simple text PDF via reportlab not available -> return a text-like PDF header to avoid crash
        return b"%PDF-1.4\n% PDF generation requires 'reportlab' installed."

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 25 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(25 * mm, y, "Student Performance Report")
    y -= 12 * mm

    c.setFont("Helvetica", 11)
    c.drawString(25 * mm, y, f"Student: {name}")
    y -= 7 * mm
    c.drawString(25 * mm, y, f"Record ID: {record_id}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(25 * mm, y, "Inputs")
    y -= 7 * mm
    c.setFont("Helvetica", 11)
    for label, key in [
        ("Attendance (%)", "attendance"),
        ("Marks (%)", "marks"),
        ("Assignments (%)", "assignments"),
        ("Study Hours (per week)", "study_hours"),
        ("Extracurriculars (0–10)", "extracurriculars"),
    ]:
        c.drawString(25 * mm, y, f"{label}: {data[key]}")
        y -= 6 * mm

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(25 * mm, y, f"Predicted Grade: {grade}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(25 * mm, y, "Recommendations")
    y -= 7 * mm
    c.setFont("Helvetica", 11)
    if recommendations:
        for r in recommendations:
            c.drawString(28 * mm, y, f"- {r}")
            y -= 6 * mm
            if y < 20 * mm:
                c.showPage()
                y = height - 25 * mm
    else:
        c.drawString(28 * mm, y, "- Keep it up!")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


# Router
if not st.session_state.auth["logged_in"]:
    st.title("Advanced Student Performance Tracker")
    welcome_card()
else:
    role = st.session_state.auth["role"]
    if role == "Student":
        student_dashboard()
    elif role == "Teacher":
        teacher_dashboard()
    else:
        st.error("Unknown role. Please logout and login again.")

st.markdown("</div>", unsafe_allow_html=True)
