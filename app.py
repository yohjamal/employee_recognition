"""
app.py
------
Employee of the Month — Recognition System
Built with Streamlit | Portfolio Project

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# Make utils importable
sys.path.insert(0, os.path.dirname(__file__))
from utils.scoring_engine import (
    validate_dataframe, select_winner, save_winner,
    get_history_df, DEFAULT_WEIGHTS, REQUIRED_COLUMNS
)
from utils.charts import (
    score_bar_chart, score_breakdown_radar,
    department_avg_bar, metric_contribution_pie, history_line_chart
)
from utils.email_notifier import notify_winner


# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Employee of the Month",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  /* Main background */
  .main { background-color: #F8FAFC; }

  /* Metric cards */
  [data-testid="metric-container"] {
    background-color: white;
    border: 1px solid #E0EDFB;
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(27,94,150,0.07);
  }

  /* Winner banner */
  .winner-banner {
    background: linear-gradient(135deg, #1B5E96 0%, #2E75B6 100%);
    border-radius: 14px;
    padding: 30px 36px;
    color: white;
    text-align: center;
    box-shadow: 0 6px 24px rgba(27,94,150,0.25);
    margin-bottom: 24px;
  }
  .winner-banner h1 { color: white; font-size: 2rem; margin: 0 0 4px 0; }
  .winner-banner h3 { color: rgba(255,255,255,0.85); font-weight: normal; margin: 0 0 12px 0; }
  .winner-score {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    border-radius: 50px;
    padding: 6px 22px;
    font-size: 1.4rem;
    font-weight: bold;
    letter-spacing: 1px;
  }

  /* Section headers */
  .section-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1B5E96;
    border-left: 4px solid #1B5E96;
    padding-left: 10px;
    margin: 20px 0 12px 0;
  }

  /* Ineligible tag */
  .tag-ineligible {
    background: #FFE0E0; color: #C62828;
    border-radius: 4px; padding: 2px 8px;
    font-size: 12px; font-weight: 600;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] { background-color: #F0F7FF; }

  /* Hide default header */
  header[data-testid="stHeader"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR — Settings & Upload
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/trophy.png", width=64)
    st.title("Recognition System")
    st.caption("Employee of the Month | HR Portfolio")
    st.divider()

    # ── File Upload ──
    st.subheader("📁 Upload Data")
    uploaded_file = st.file_uploader(
        "Upload employee CSV or Excel",
        type=["csv", "xlsx"],
        help=f"Required columns: {', '.join(REQUIRED_COLUMNS)}"
    )

    st.download_button(
        label="⬇️ Download sample CSV",
        data=open(os.path.join(os.path.dirname(__file__), "data", "employees_sample.csv")).read(),
        file_name="employees_sample.csv",
        mime="text/csv",
    )

    st.divider()

    # ── Scoring Weights ──
    st.subheader("⚖️ Scoring Weights")
    st.caption("Adjust how each metric contributes to the final score. Must total 100%.")

    w_perf  = st.slider("Performance Score",  0, 100, 40, step=5)
    w_peer  = st.slider("Peer Nominations",   0, 100, 30, step=5)
    w_att   = st.slider("Attendance %",       0, 100, 20, step=5)
    w_mgr   = st.slider("Manager Rating",     0, 100, 10, step=5)

    total_w = w_perf + w_peer + w_att + w_mgr
    if total_w != 100:
        st.error(f"Weights sum to {total_w}% — must equal 100%.")
        weights_valid = False
    else:
        st.success("✅ Weights valid")
        weights_valid = True

    weights = {
        "performance_score": w_perf / 100,
        "peer_nominations":  w_peer / 100,
        "attendance_pct":    w_att  / 100,
        "manager_rating":    w_mgr  / 100,
    }

    st.divider()

    # ── Month Label ──
    st.subheader("📅 Award Month")
    award_month = st.text_input(
        "Month label",
        value=datetime.now().strftime("%B %Y"),
        help="This label appears in emails and history."
    )

    st.divider()

    # ── Email Config (optional) ──
    with st.expander("📧 Email Settings (optional)"):
        hr_email      = st.text_input("HR Manager Email", placeholder="hr@company.com")
        sender_email  = st.text_input("Sender Gmail",     placeholder="noreply@gmail.com")
        sender_pass   = st.text_input("App Password",     type="password",
                                       help="Use a Gmail App Password, not your account password.")
        smtp_config = {
            "host": "smtp.gmail.com",
            "port": 465,
            "sender_email": sender_email,
            "sender_password": sender_pass,
        }
        email_ready = bool(hr_email and sender_email and sender_pass)


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
df_raw = None

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)

        valid, msg = validate_dataframe(df_raw)
        if not valid:
            st.error(f"❌ Data validation failed: {msg}")
            df_raw = None

    except Exception as e:
        st.error(f"Could not read file: {e}")
        df_raw = None


# ─────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────
if df_raw is None:

    # ── Landing / Welcome screen ──
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px;">
      <div style="font-size: 72px; margin-bottom: 12px;">🏆</div>
      <h1 style="color: #1B5E96; font-size: 2.2rem;">Employee of the Month</h1>
      <p style="color: #666; font-size: 1.1rem; max-width: 560px; margin: 10px auto 30px;">
        An automated, data-driven recognition system. Upload your employee data
        to run the scoring engine, view the leaderboard, and notify the winner.
      </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    for col, icon, title, desc in [
        (col1, "📂", "Upload Data",     "CSV or Excel with employee metrics"),
        (col2, "⚖️", "Configure Weights", "Customise scoring criteria"),
        (col3, "📊", "View Dashboard",  "Rankings, radar charts, department breakdown"),
        (col4, "📧", "Notify Winner",   "Auto-send congratulations email"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:white; border-radius:10px; padding:20px;
                        text-align:center; border: 1px solid #E0EDFB;
                        box-shadow: 0 2px 8px rgba(27,94,150,0.07);">
              <div style="font-size:32px">{icon}</div>
              <p style="font-weight:700; color:#1B5E96; margin:8px 0 4px;">{title}</p>
              <p style="color:#888; font-size:13px; margin:0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.info("👈 Upload a CSV file using the sidebar to get started. Download the sample file to see the required format.")

else:
    # ── Run scoring engine ──
    if not weights_valid:
        st.error("Fix the scoring weights in the sidebar before proceeding.")
        st.stop()

    winner, df_scored = select_winner(df_raw, weights)


    # ══════════════════════════════════════════
    # TAB LAYOUT
    # ══════════════════════════════════════════
    tab1, tab2, tab3 = st.tabs(["🏆 Results", "📊 Analytics", "📜 History"])


    # ─────────────────────────────────────────
    # TAB 1 — RESULTS
    # ─────────────────────────────────────────
    with tab1:

        if winner is None:
            st.warning("⚠️ No eligible employees found. Check tenure requirements and previous winner exclusions.")
        else:
            # Winner banner
            st.markdown(f"""
            <div class="winner-banner">
              <div style="font-size:52px; margin-bottom:8px;">🏆</div>
              <h1>{winner['name']}</h1>
              <h3>{winner['department']} Department</h3>
              <div class="winner-score">{winner['composite_score']:.1f} / 100</div>
              <p style="margin:12px 0 0; opacity:0.75; font-size:14px;">Employee of the Month — {award_month}</p>
            </div>
            """, unsafe_allow_html=True)

            # Key metrics row
            eligible_df = df_scored[df_scored["eligible"]]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("👥 Employees Evaluated", len(df_scored))
            c2.metric("✅ Eligible",             len(eligible_df))
            c3.metric("🏅 Winner Score",         f"{winner['composite_score']:.1f}")
            c4.metric("🥈 Runner-up Score",
                       f"{eligible_df.nlargest(2, 'composite_score').iloc[-1]['composite_score']:.1f}"
                       if len(eligible_df) > 1 else "—")

            st.markdown('<p class="section-title">Full Leaderboard</p>', unsafe_allow_html=True)

            # Leaderboard table
            display_cols = ["rank", "name", "department", "composite_score",
                            "performance_score", "peer_nominations",
                            "attendance_pct", "manager_rating", "eligible", "ineligibility_reason"]
            display_df = df_scored[display_cols].copy()
            display_df = display_df.sort_values("composite_score", ascending=False)
            display_df.columns = ["Rank", "Name", "Department", "Score",
                                   "Performance", "Peer Nom.", "Attendance%",
                                   "Mgr Rating", "Eligible", "Reason"]

            st.dataframe(
                display_df.style
                    .format({"Score": "{:.2f}", "Performance": "{:.0f}",
                             "Attendance%": "{:.0f}%"})
                    .apply(lambda row: [
                        "background-color: #E8F4FD; font-weight: 600;"
                        if row["Name"] == winner["name"] else ""
                    ] * len(row), axis=1),
                use_container_width=True,
                height=350,
            )

            # Score bar chart
            st.plotly_chart(score_bar_chart(df_scored), use_container_width=True)

            # ── Email section ──
            st.markdown('<p class="section-title">📧 Notify Winner</p>', unsafe_allow_html=True)

            if not email_ready:
                st.info("Configure email settings in the sidebar to send automated notifications.")
            else:
                col_send, col_preview = st.columns([1, 3])
                with col_send:
                    if st.button("🚀 Send Notifications", type="primary", use_container_width=True):
                        with st.spinner("Sending emails..."):
                            results = notify_winner(
                                winner=winner,
                                month=award_month,
                                total_employees=len(df_scored),
                                smtp_config=smtp_config,
                                hr_email=hr_email,
                            )
                        for r in results:
                            if r["success"]:
                                st.success(f"✅ {r['message']}")
                            else:
                                st.error(f"❌ {r['recipient']}: {r['message']}")

            # ── Save winner button ──
            st.markdown('<p class="section-title">💾 Save to History</p>', unsafe_allow_html=True)
            if st.button("Save Winner to History", use_container_width=False):
                save_winner(winner, award_month)
                st.success(f"✅ {winner['name']} saved as {award_month} winner!")
                st.rerun()


    # ─────────────────────────────────────────
    # TAB 2 — ANALYTICS
    # ─────────────────────────────────────────
    with tab2:
        st.markdown('<p class="section-title">Winner Performance Breakdown</p>',
                    unsafe_allow_html=True)

        if winner is not None:
            col_radar, col_pie = st.columns(2)
            with col_radar:
                st.plotly_chart(score_breakdown_radar(winner, weights), use_container_width=True)
            with col_pie:
                st.plotly_chart(metric_contribution_pie(winner, weights), use_container_width=True)

        st.markdown('<p class="section-title">Department Analysis</p>', unsafe_allow_html=True)
        st.plotly_chart(department_avg_bar(df_scored), use_container_width=True)

        # Metric summary table
        st.markdown('<p class="section-title">Metric Averages by Department</p>',
                    unsafe_allow_html=True)
        dept_summary = df_scored.groupby("department").agg(
            Employees=("name", "count"),
            Avg_Score=("composite_score", "mean"),
            Avg_Performance=("performance_score", "mean"),
            Avg_Attendance=("attendance_pct", "mean"),
            Avg_Manager_Rating=("manager_rating", "mean"),
        ).round(1).reset_index()
        st.dataframe(dept_summary, use_container_width=True)

        # Bias check
        st.markdown('<p class="section-title">⚠️ Fairness Check</p>', unsafe_allow_html=True)
        st.caption(
            "Good HR practice requires checking for systematic bias in scoring. "
            "Review whether any department is consistently under/over-represented."
        )
        dept_wins = get_history_df()
        if not dept_wins.empty and "department" in dept_wins.columns:
            win_counts = dept_wins["department"].value_counts().reset_index()
            win_counts.columns = ["Department", "Times Won"]
            st.dataframe(win_counts, use_container_width=True)
        else:
            st.info("Run the system for multiple months to see department win distribution here.")


    # ─────────────────────────────────────────
    # TAB 3 — HISTORY
    # ─────────────────────────────────────────
    with tab3:
        st.markdown('<p class="section-title">Winner History</p>', unsafe_allow_html=True)

        history_df = get_history_df()

        if history_df.empty:
            st.info("No winners saved yet. Run the scoring engine and click 'Save Winner to History'.")
        else:
            st.plotly_chart(history_line_chart(history_df), use_container_width=True)

            display_history = history_df[["month", "name", "department", "composite_score"]].copy()
            display_history.columns = ["Month", "Winner", "Department", "Score"]
            st.dataframe(
                display_history.style.format({"Score": "{:.2f}"}),
                use_container_width=True
            )

            # Export history
            csv = history_df.to_csv(index=False)
            st.download_button(
                "⬇️ Export History CSV",
                data=csv,
                file_name="winner_history.csv",
                mime="text/csv"
            )
