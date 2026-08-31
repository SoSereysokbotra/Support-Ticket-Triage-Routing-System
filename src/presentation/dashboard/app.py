"""
Streamlit MLOps Monitoring & Drift Dashboard
Provides real-time visibility into production inference traffic, confidence trends,
feature/target drift reports (Evidently AI), and closed-loop retraining triggers.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path for Streamlit runner
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

# Configure page
st.set_page_config(
    page_title="Support Ticket Triage — MLOps Monitoring",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        color: #ffffff;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin-top: 4px;
        color: #38bdf8;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_monitoring_data():
    from src.infrastructure.monitoring.prediction_logger import PredictionLogger
    logger = PredictionLogger()
    df = logger.get_recent_logs(limit=2000)
    summary = logger.get_summary_metrics()
    return df, summary


def main():
    st.title("🛡️ Support Ticket MLOps Monitoring Dashboard")
    st.caption("Live Inference Telemetry • Statistical Drift Detection (Evidently AI) • Automated Self-Healing Trigger")

    df, summary = load_monitoring_data()

    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Controls")
        auto_refresh = st.checkbox("Auto-refresh Data", value=True)
        sample_limit = st.slider("Max Logs to Inspect", min_value=100, max_value=2000, value=500, step=100)
        
        st.divider()
        st.subheader("🚨 Drift Simulation Tool")
        st.write("Inject Out-Of-Distribution traffic (e.g. Legal/Crypto jargon) to demonstrate automated drift detection and closed-loop retraining.")
        
        if st.button("🧪 Inject Synthetic Drift Batch", type="primary"):
            with st.spinner("Injecting 50 out-of-distribution tickets..."):
                from src.infrastructure.monitoring.prediction_logger import PredictionLogger
                logger = PredictionLogger()
                
                drift_texts = [
                    "Liquidity pool staking rewards yield farming smart contract vulnerability audit",
                    "Class action lawsuit arbitration clause breach of fiduciary duty litigation settlement",
                    "Cross-chain bridge tokenomics zero-knowledge proof gas fee arbitrage",
                    "Securities and Exchange Commission subpoena deposition deposition transcript discovery",
                    "MEV bot front-running decentralized exchange slippage tolerance liquidation",
                ] * 10
                
                records = [
                    {
                        "ticket_id": f"DRIFT-{i:04d}",
                        "text": txt,
                        "predicted_category": "Other",
                        "confidence": 0.42 + (i % 10) * 0.03,
                        "latency_ms": 32.5,
                        "customer_id": f"CUST-DRIFT-{i}",
                        "model_version": "v1",
                    }
                    for i, txt in enumerate(drift_texts)
                ]
                logger.log_batch(records)
                st.success("Injected 50 drifted records! Click 'Run Drift Analysis' to see Evidently detection.")
                st.rerun()

    # Top KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    total_reqs = summary.get("total_requests", 0)
    avg_conf = summary.get("avg_confidence", 0.0)
    avg_lat = summary.get("avg_latency_ms", 0.0)
    
    with col1:
        st.markdown(
            f"""<div class="kpi-card"><div class="kpi-label">Total Inferences</div><div class="kpi-value">{total_reqs:,}</div></div>""",
            unsafe_allow_html=True,
        )
    with col2:
        conf_color = "#10b981" if avg_conf >= 0.85 else "#f59e0b" if avg_conf >= 0.70 else "#ef4444"
        st.markdown(
            f"""<div class="kpi-card"><div class="kpi-label">Avg Confidence</div><div class="kpi-value" style="color: {conf_color}">{avg_conf:.1%}</div></div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class="kpi-card"><div class="kpi-label">Avg Latency</div><div class="kpi-value">{avg_lat:.1f} ms</div></div>""",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""<div class="kpi-card"><div class="kpi-label">Active Model Alias</div><div class="kpi-value" style="font-size: 1.5rem; color: #a855f7;">production (v1)</div></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab_traffic, tab_drift, tab_reports = st.tabs(["📊 Live Telemetry & Trends", "🔍 Drift Detection Analysis", "📑 Evidently AI Reports"])

    with tab_traffic:
        if df.empty:
            st.info("No inference logs recorded yet. Send requests to FastAPI `/api/v1/predict` or use the sidebar simulation tool.")
        else:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("Predicted Category Distribution")
                cat_counts = df["predicted_category"].value_counts().reset_index()
                cat_counts.columns = ["Category", "Count"]
                st.bar_chart(cat_counts.set_index("Category"))

            with col_chart2:
                st.subheader("Inference Confidence Over Time")
                if "timestamp" in df.columns and "confidence" in df.columns:
                    chart_df = df[["timestamp", "confidence"]].copy()
                    chart_df = chart_df.set_index("timestamp")
                    st.line_chart(chart_df)

            st.subheader("Recent Production Requests")
            st.dataframe(
                df[["ticket_id", "timestamp", "text", "predicted_category", "confidence", "latency_ms", "customer_id", "model_version"]].tail(50),
                use_container_width=True,
            )

    with tab_drift:
        st.subheader("Statistical Drift Analysis Engine")
        st.write("Calculates Kolmogorov-Smirnov, Wasserstein, and Chi-Square / PSI metrics comparing live traffic vs baseline reference.")

        if st.button("🚀 Run Drift Detection Check Now"):
            with st.spinner("Analyzing data & target distributions..."):
                from src.infrastructure.monitoring.drift_detector import DriftDetector
                detector = DriftDetector()
                report_res = detector.analyze_drift(df, generate_html=True)

                if report_res.drift_detected:
                    st.error(f"🚨 **DRIFT DETECTED!** Share of drifted features: **{report_res.share_drifted_features:.1%}**")
                else:
                    st.success(f"✅ **Distributions Healthy.** Share of drifted features: **{report_res.share_drifted_features:.1%}** (Below threshold)")

                # Metric cards
                st.write("### Feature Metric Results")
                m_cols = st.columns(len(report_res.metric_results) + (1 if report_res.target_drift else 0))
                idx = 0
                for col_name, m_res in report_res.metric_results.items():
                    with m_cols[idx]:
                        status_str = "🚨 Drift" if m_res.drift_detected else "✅ Normal"
                        st.metric(
                            label=f"{col_name} ({m_res.stat_test})",
                            value=status_str,
                            delta=f"p-val: {m_res.p_value:.4f}" if m_res.p_value is not None else "N/A",
                            delta_color="normal" if not m_res.drift_detected else "inverse",
                        )
                    idx += 1

                if report_res.target_drift:
                    with m_cols[idx]:
                        t_res = report_res.target_drift
                        st.metric(
                            label="Target Drift (PSI)",
                            value="🚨 Drift" if t_res.drift_detected else "✅ Normal",
                            delta=f"PSI: {t_res.drift_score:.3f}",
                            delta_color="normal" if not t_res.drift_detected else "inverse",
                        )

    with tab_reports:
        st.subheader("Evidently AI Reports Archive")
        reports_dir = Path("data/monitoring/reports")
        if reports_dir.exists():
            html_files = sorted(reports_dir.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
            if html_files:
                selected_report = st.selectbox("Select Report Snapshot", [f.name for f in html_files])
                if selected_report:
                    report_path = reports_dir / selected_report
                    st.download_button(
                        label="📥 Download HTML Report",
                        data=report_path.read_text(encoding="utf-8"),
                        file_name=selected_report,
                        mime="text/html",
                    )
                    st.components.v1.html(report_path.read_text(encoding="utf-8"), height=700, scrolling=True)
            else:
                st.info("No Evidently reports generated yet. Run a drift check to generate one.")
        else:
            st.info("No reports directory found.")


if __name__ == "__main__":
    main()
