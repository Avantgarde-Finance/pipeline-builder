import io
import re
import zipfile
import streamlit as st
from generators import (
    generate_serverless_yml,
    generate_dockerfile,
    generate_buildsh,
    generate_migration_sql,
    generate_github_deploy_ecr,
    generate_github_deploy_staging,
    generate_github_deploy_prod,
    generate_github_apply_migration,
    generate_github_oidc_role_cfn,
    generate_readme,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pipeline Builder · Serverless",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;800&display=swap');

:root {
    --bg:#0a0a0f; --surface:#111118; --border:#1e1e2e; --accent:#7c3aed;
    --accent-glow:rgba(124,58,237,0.25); --green:#10b981; --amber:#f59e0b;
    --blue:#3b82f6; --text:#e2e8f0; --muted:#64748b;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text);
    font-family: 'Syne', sans-serif;
}
[data-testid="stAppViewContainer"]::before {
    content: ''; position: fixed; top: -40%; left: -20%;
    width: 80vw; height: 80vh;
    background: radial-gradient(ellipse, rgba(124,58,237,0.07) 0%, transparent 70%);
    pointer-events: none; z-index: 0;
}
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

.top-banner {
    background: linear-gradient(135deg, rgba(124,58,237,0.15), rgba(16,185,129,0.06));
    border: 1px solid rgba(124,58,237,0.3); border-radius: 14px;
    padding: 22px 28px; margin-bottom: 28px;
}
.step-header {
    display: flex; align-items: center; gap: 14px;
    margin: 32px 0 18px; padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
}
.step-num {
    background: var(--accent); color: white; width: 30px; height: 30px;
    border-radius: 8px; display: flex; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 13px; flex-shrink: 0;
}
.step-title { font-weight: 800; font-size: 17px; letter-spacing: -0.3px; }

.badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600;
    background: rgba(124,58,237,0.2); color: #a78bfa; border: 1px solid rgba(124,58,237,0.3);
}
.badge-green { background: rgba(16,185,129,0.15); color: #6ee7b7; border-color: rgba(16,185,129,0.3); }
.badge-amber { background: rgba(245,158,11,0.15); color: #fcd34d; border-color: rgba(245,158,11,0.3); }
.badge-blue  { background: rgba(59,130,246,0.15); color: #93c5fd;  border-color: rgba(59,130,246,0.3); }

.info-box {
    background: rgba(124,58,237,0.07); border: 1px solid rgba(124,58,237,0.22);
    border-radius: 10px; padding: 13px 17px;
    font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #c4b5fd; margin: 10px 0;
}
.warn-box {
    background: rgba(245,158,11,0.07); border: 1px solid rgba(245,158,11,0.25);
    border-radius: 10px; padding: 13px 17px; font-size: 12px; color: #fcd34d; margin: 10px 0;
}
.success-box {
    background: rgba(16,185,129,0.07); border: 1px solid rgba(16,185,129,0.25);
    border-radius: 10px; padding: 13px 17px; font-size: 12px; color: #6ee7b7; margin: 10px 0;
}
.file-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.25);
    border-radius: 6px; padding: 4px 10px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #93c5fd; margin: 3px;
}
.file-tree {
    background: #0d0d14; border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 20px;
    font-family: 'JetBrains Mono', monospace; font-size: 12px; line-height: 2; color: var(--text);
}
.file-tree .dir  { color: #7c3aed; font-weight: 700; }
.file-tree .key  { color: #10b981; }
.file-tree .muted { color: var(--muted); font-size: 11px; }

.cicd-step {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 20px 16px 52px; margin: 8px 0; position: relative;
}
.cicd-step-num {
    position: absolute; left: 16px; top: 16px; background: var(--accent);
    color: white; width: 24px; height: 24px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700;
}
.cicd-step-title { font-weight: 700; font-size: 14px; margin-bottom: 6px; }
.cicd-step-body  { font-size: 13px; color: #94a3b8; line-height: 1.6; }

/* Streamlit widget overrides */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 13px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-glow) !important;
}
.stButton > button {
    background: var(--accent) !important; color: white !important; border: none !important;
    border-radius: 8px !important; font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 13px !important; padding: 9px 20px !important;
    transition: all 0.15s !important;
}
.stButton > button:hover { background: #6d28d9 !important; transform: translateY(-1px) !important; }
.stCheckbox > label { color: var(--text) !important; font-size: 13px !important; }
.stSelectbox label, .stTextInput label, .stTextArea label,
.stSlider label, .stNumberInput label {
    color: var(--muted) !important; font-size: 11px !important;
    font-family: 'JetBrains Mono', monospace !important;
    text-transform: uppercase !important; letter-spacing: 0.5px !important;
}
div[data-testid="stExpander"] {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
[data-testid="stTabs"] button {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important; color: var(--muted) !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent) !important; border-bottom-color: var(--accent) !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 800 !important;
    font-size: 15px !important; padding: 14px 32px !important; width: 100% !important;
    box-shadow: 0 4px 24px rgba(16,185,129,0.3) !important;
}
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-banner">
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
    <div>
      <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:24px;letter-spacing:-0.5px;">
        ⚡ Pipeline Builder <span style="color:#7c3aed;">· Serverless Framework</span>
      </div>
      <div style="color:#64748b;font-family:'JetBrains Mono',monospace;font-size:11px;margin-top:5px;">
        Pick your components → configure → generate a complete deployable repo
      </div>
    </div>
    <div style="margin-left:auto;display:flex;gap:6px;flex-wrap:wrap;">
      <span class="badge-green badge">serverless.yml</span>
      <span class="badge-amber badge">ECR + Lambda</span>
      <span class="badge badge">staging → prod</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_build, tab_cicd = st.tabs(["🔧  Build Pipeline", "🚀  CI/CD Setup Guide"])

# ── Session state init ─────────────────────────────────────────────────────────
if "env_vars" not in st.session_state:
    st.session_state.env_vars = []
if "db_columns" not in st.session_state:
    st.session_state.db_columns = [
        {"name": "id",         "type": "BIGSERIAL",   "pk": True,  "nullable": False, "default": ""},
        {"name": "created_at", "type": "TIMESTAMPTZ", "pk": False, "nullable": False, "default": "NOW()"},
    ]
if "sel" not in st.session_state:
    st.session_state.sel = {}
if "helper_dirs" not in st.session_state:
    st.session_state.helper_dirs = []  # ordered list of subdirectory names the user created


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BUILD PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
with tab_build:

    # ── STEP 1 — Component Picker ──────────────────────────────────────────────
    st.markdown(
        '<div class="step-header">'
        '<div class="step-num">1</div>'
        '<div class="step-title">Choose Your Pipeline Components</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="color:#64748b;font-size:13px;margin-bottom:16px;">'
        'Select the AWS services you want in this pipeline. '
        'Lambda is always included as the compute layer.'
        '</div>',
        unsafe_allow_html=True,
    )

    COMPONENTS = [
        {"key": "lambda",      "icon": "λ",   "name": "Lambda",         "desc": "Python compute. Always included.", "required": True},
        {"key": "eventbridge", "icon": "⏰",  "name": "EventBridge",    "desc": "Schedule trigger (rate or cron)",  "required": False},
        {"key": "sns_trigger", "icon": "📣",  "name": "SNS Trigger",    "desc": "Subscribe Lambda to SNS topic",    "required": False},
        {"key": "sqs",         "icon": "📬",  "name": "SQS Queue",      "desc": "Queue trigger + batch processing", "required": False},
        {"key": "api_gateway", "icon": "🌐",  "name": "API Gateway",    "desc": "HTTP endpoint (HTTP API v2)",      "required": False},
        {"key": "sns_failure", "icon": "🚨",  "name": "Failure Alerts", "desc": "SNS topic for failed invocations", "required": False},
        {"key": "rds",         "icon": "🗄️", "name": "Postgres / RDS", "desc": "Target table + migration SQL",     "required": False},
        {"key": "s3",          "icon": "🪣",  "name": "S3",             "desc": "S3 read/write + IAM policy",       "required": False},
        {"key": "xray",        "icon": "🔍",  "name": "X-Ray Tracing",  "desc": "Distributed tracing for Lambda",   "required": False},
    ]

    sel = {}
    cols = st.columns(3)
    for i, comp in enumerate(COMPONENTS):
        with cols[i % 3]:
            if comp["required"]:
                st.checkbox(
                    f"{comp['icon']}  **{comp['name']}** — *{comp['desc']}*",
                    value=True, disabled=True, key=f"comp_req_{comp['key']}",
                )
                sel[comp["key"]] = True
            else:
                default = st.session_state.sel.get(comp["key"], False)
                val = st.checkbox(
                    f"{comp['icon']}  **{comp['name']}** — *{comp['desc']}*",
                    value=default, key=f"comp_{comp['key']}",
                )
                sel[comp["key"]] = val

    st.session_state.sel = sel

    selected_names = [c["name"] for c in COMPONENTS if sel.get(c["key"])]
    chips = "".join([f'<span class="badge" style="margin:2px;">{n}</span>' for n in selected_names])
    st.markdown(
        f'<div style="margin-top:8px;">'
        f'<span style="color:#64748b;font-size:11px;font-family:\'JetBrains Mono\',monospace;'
        f'text-transform:uppercase;letter-spacing:0.5px;">Pipeline includes:</span> {chips}</div>',
        unsafe_allow_html=True,
    )

    # ── STEP 2 — Pipeline Identity ─────────────────────────────────────────────
    st.markdown(
        '<div class="step-header"><div class="step-num">2</div>'
        '<div class="step-title">Pipeline Identity</div></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([2, 1.5, 1])
    with c1:
        pipeline_name = st.text_input("Pipeline name", value="arbitrum-block-fetcher",
                                       help="Becomes the Serverless service name and repo folder")
        slug = re.sub(r"[^a-z0-9-]", "-", pipeline_name.lower()).strip("-") or "my-pipeline"
    with c2:
        aws_region = st.selectbox("AWS Region", ["eu-west-1", "us-east-1", "us-west-2", "ap-southeast-1", "ap-northeast-1"])
    with c3:
        prod_stage = st.selectbox("Prod stage name", ["prod", "production", "main"])

    c1, c2 = st.columns(2)
    with c1:
        aws_account_id = st.text_input("AWS Account ID", value="123456789012")
    with c2:
        ecr_repo_name = st.text_input("ECR Repository name", value=slug)

    # ── STEP 3 — Configure Triggers ────────────────────────────────────────────
    trigger_type   = "none"
    schedule_expr  = ""
    sns_topic_arn  = ""
    sqs_arn        = ""
    sqs_batch_size = 10
    http_path      = "/run"
    http_method    = "GET"

    has_trigger = any(sel.get(k) for k in ["eventbridge", "sns_trigger", "sqs", "api_gateway"])
    if has_trigger:
        st.markdown(
            '<div class="step-header"><div class="step-num">3</div>'
            '<div class="step-title">Configure Trigger(s)</div></div>',
            unsafe_allow_html=True,
        )

        if sel.get("eventbridge"):
            st.markdown("##### ⏰ EventBridge Schedule")
            trigger_type = "schedule"
            c1, c2 = st.columns([1, 2])
            with c1:
                schedule_mode = st.radio("Mode", ["Rate", "Cron"], horizontal=True)
            with c2:
                if schedule_mode == "Rate":
                    r1, r2 = st.columns(2)
                    with r1:
                        rate_val = st.number_input("Every N", min_value=1, value=1)
                    with r2:
                        rate_unit = st.selectbox("Unit", ["hour", "hours", "day", "days", "minute", "minutes"])
                    schedule_expr = f"rate({rate_val} {rate_unit})"
                else:
                    c1b, c2b, c3b, c4b, c5b = st.columns(5)
                    with c1b: m   = st.text_input("Min",  "0")
                    with c2b: h   = st.text_input("Hour", "2")
                    with c3b: dom = st.text_input("DoM",  "*")
                    with c4b: mon = st.text_input("Mon",  "*")
                    with c5b: dow = st.text_input("DoW",  "?")
                    schedule_expr = f"cron({m} {h} {dom} {mon} {dow} *)"
            st.markdown(
                f'<div class="info-box">serverless.yml event: <b>schedule: {schedule_expr}</b></div>',
                unsafe_allow_html=True,
            )

        if sel.get("sns_trigger"):
            st.markdown("##### 📣 SNS Trigger")
            if trigger_type == "none":
                trigger_type = "sns"
            sns_topic_arn = st.text_input("SNS Topic ARN", "arn:aws:sns:eu-west-1:123456789012:my-topic")

        if sel.get("sqs"):
            st.markdown("##### 📬 SQS Queue")
            if trigger_type == "none":
                trigger_type = "sqs"
            c1, c2 = st.columns(2)
            with c1:
                sqs_arn = st.text_input("SQS Queue ARN", "arn:aws:sqs:eu-west-1:123456789012:my-queue")
            with c2:
                sqs_batch_size = st.number_input("Batch size", 1, 10000, 10)

        if sel.get("api_gateway"):
            st.markdown("##### 🌐 API Gateway")
            if trigger_type == "none":
                trigger_type = "http"
            c1, c2 = st.columns(2)
            with c1:
                http_path = st.text_input("Path", "/run")
            with c2:
                http_method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])

    # ── STEP 4 — Lambda Config ─────────────────────────────────────────────────
    st.markdown(
        '<div class="step-header"><div class="step-num">4</div>'
        '<div class="step-title">Lambda Configuration</div></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        memory = st.select_slider("Memory (MB)", options=[128, 256, 512, 1024, 2048, 3008, 4096, 8192, 10240], value=256)
    with c2:
        timeout = st.slider("Timeout (seconds)", 10, 900, 300)
    with c3:
        architecture = st.selectbox("Architecture", ["x86_64", "arm64"])

    c1, c2 = st.columns(2)
    with c1:
        python_runtime = st.selectbox("Python version", ["python3.12", "python3.11", "python3.10"])
    with c2:
        reserved_concurrency = st.number_input("Reserved concurrency (-1 = unreserved)", min_value=-1, value=-1)

    keep_warm = st.checkbox("Provisioned concurrency (keep warm)", value=False)

    # ── STEP 5 — Environment Variables ────────────────────────────────────────
    st.markdown(
        '<div class="step-header"><div class="step-num">5</div>'
        '<div class="step-title">Environment Variables</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="info-box">'
        'Prefix values with <b>ssm:</b> to resolve from SSM Parameter Store at deploy time — '
        'secrets never touch the repo.<br>'
        'e.g. <code>DB_PASSWORD</code> → <code>ssm:/app/prod/db-password</code>'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button("＋ Add variable", key="add_env"):
        st.session_state.env_vars.append({"key": "", "value": ""})

    for i, ev in enumerate(st.session_state.env_vars):
        c1, c2, c3 = st.columns([2, 3, 0.4])
        with c1:
            st.session_state.env_vars[i]["key"] = st.text_input("Key", ev["key"], key=f"ek_{i}")
        with c2:
            val = st.text_input("Value", ev["value"], key=f"ev_{i}")
            st.session_state.env_vars[i]["value"] = val
            if val.startswith("ssm:"):
                st.markdown('<span class="badge-amber badge">SSM secret</span>', unsafe_allow_html=True)
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✕", key=f"rm_{i}"):
                st.session_state.env_vars.pop(i)
                st.rerun()

    s3_bucket = ""
    if sel.get("s3"):
        s3_bucket = st.text_input("S3 bucket name (added to IAM policy)", "my-pipeline-bucket")

    # ── STEP 6 — Lambda Code & Helper Files ───────────────────────────────────
    st.markdown(
        '<div class="step-header"><div class="step-num">6</div>'
        '<div class="step-title">Lambda Code & Helper Files</div></div>',
        unsafe_allow_html=True,
    )

    default_handler = '''\
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Entry point. Replace with your actual fetch / transform / write logic.
    """
    logger.info("Event: %s", json.dumps(event))

    # ── Your logic here ────────────────────────────────────────────────────
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ok",
    }

    logger.info("Done: %s", result)
    return result
'''

    default_requirements = """\
web3>=6.0.0
psycopg2-binary>=2.9.9
boto3>=1.34.0
requests>=2.31.0
"""

    handler_code     = st.text_area("handler.py", default_handler, height=260)
    requirements_txt = st.text_area("requirements.txt", default_requirements, height=110)

    st.markdown("#### 📎 Helper Files")
    st.markdown(
        '<div class="info-box">'
        'Create named subdirectories below, then upload files into each one. '
        'Files under <b>lambda/ root</b> sit directly alongside <code>handler.py</code>. '
        'Each directory gets its own <code>COPY</code> layer in the Dockerfile — '
        'e.g. a <code>utils/</code> dir imports as <code>from utils.db import ...</code>.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Root-level helper files ────────────────────────────────────────────────
    st.markdown("**📂 `lambda/` root** — same level as `handler.py`")
    root_helper_files = st.file_uploader(
        "Upload files to place directly in lambda/",
        accept_multiple_files=True,
        type=["py", "json", "yaml", "yml", "env", "sql", "txt", "sh"],
        key="files_root",
    )

    st.markdown("---")

    # ── Directory management ───────────────────────────────────────────────────
    st.markdown("**📁 Subdirectories**")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.text_input(
            "New directory name",
            key="new_dir_input",
            placeholder="e.g. utils, models, abi",
        )
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("＋ Create directory"):
            name = st.session_state.new_dir_input.strip("/").strip()
            if name and name not in st.session_state.helper_dirs:
                st.session_state.helper_dirs.append(name)
                st.rerun()

    for i, dir_name in enumerate(list(st.session_state.helper_dirs)):
        with st.expander(f"📁  lambda/{dir_name}/", expanded=True):
            st.caption(f"Files here import as `from {dir_name}.module import ...`")
            st.file_uploader(
                f"Upload files for lambda/{dir_name}/",
                accept_multiple_files=True,
                type=["py", "json", "yaml", "yml", "env", "sql", "txt", "sh"],
                key=f"files_dir_{dir_name}",
            )
            if st.button(f"✕  Remove lambda/{dir_name}/", key=f"rm_dir_{i}"):
                st.session_state.helper_dirs.pop(i)
                st.rerun()

    # ── Collect all helper file assignments ────────────────────────────────────
    all_helper_assignments: list[dict] = []
    for f in (root_helper_files or []):
        all_helper_assignments.append({"file": f, "name": f.name, "dir": ""})
    for dir_name in st.session_state.helper_dirs:
        for f in (st.session_state.get(f"files_dir_{dir_name}") or []):
            all_helper_assignments.append({"file": f, "name": f.name, "dir": dir_name})

    if all_helper_assignments:
        st.markdown(
            '<div class="success-box" style="margin-top:10px;">'
            + "".join(
                f'<span class="file-chip">📄 lambda/'
                f'{"" if not e["dir"] else e["dir"] + "/"}{e["name"]}</span>'
                for e in all_helper_assignments
            )
            + "<br>✅ Each directory gets its own <code>COPY</code> layer in the Dockerfile."
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="color:#64748b;font-size:12px;font-family:\'JetBrains Mono\',monospace;margin:6px 0;">'
            'No helper files added — only handler.py and requirements.txt will be in lambda/'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── STEP 7 — RDS / Postgres ───────────────────────────────────────────────
    db_schema = db_table = ""
    create_migration = False

    if sel.get("rds"):
        st.markdown(
            '<div class="step-header"><div class="step-num">7</div>'
            '<div class="step-title">Postgres / RDS — Target Table</div></div>',
            unsafe_allow_html=True,
        )
        create_migration = True

        c1, c2 = st.columns(2)
        with c1:
            db_schema = st.text_input("Schema", "public")
        with c2:
            db_table = st.text_input("Table name", slug.replace("-", "_"))

        st.markdown("**Table columns**")
        if st.button("＋ Add column", key="add_col"):
            st.session_state.db_columns.append(
                {"name": "", "type": "TEXT", "pk": False, "nullable": True, "default": ""}
            )

        pg_types = [
            "TEXT", "INTEGER", "BIGINT", "BIGSERIAL", "NUMERIC", "BOOLEAN",
            "TIMESTAMPTZ", "TIMESTAMP", "JSONB", "UUID", "VARCHAR(255)",
        ]

        for i, col in enumerate(st.session_state.db_columns):
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 0.7, 0.7, 2, 0.4])
            with c1:
                st.session_state.db_columns[i]["name"] = st.text_input(
                    "Column", col["name"], key=f"cn_{i}"
                )
            with c2:
                st.session_state.db_columns[i]["type"] = st.selectbox(
                    "Type", pg_types,
                    index=pg_types.index(col["type"]) if col["type"] in pg_types else 0,
                    key=f"ct_{i}",
                )
            with c3:
                st.session_state.db_columns[i]["pk"] = st.checkbox("PK", col["pk"], key=f"cpk_{i}")
            with c4:
                st.session_state.db_columns[i]["nullable"] = st.checkbox("NULL", col["nullable"], key=f"cnull_{i}")
            with c5:
                st.session_state.db_columns[i]["default"] = st.text_input(
                    "Default", col["default"], key=f"cdef_{i}"
                )
            with c6:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✕", key=f"rmc_{i}"):
                    st.session_state.db_columns.pop(i)
                    st.rerun()

        # Live SQL preview
        cols_sql, pk_cols = [], []
        for col in st.session_state.db_columns:
            if not col["name"]:
                continue
            parts = [f'    "{col["name"]}"', col["type"]]
            if col["pk"]:
                pk_cols.append(f'"{col["name"]}"')
            if not col["nullable"] and not col["pk"]:
                parts.append("NOT NULL")
            if col["default"]:
                parts.append(f"DEFAULT {col['default']}")
            cols_sql.append(" ".join(parts))
        if pk_cols:
            cols_sql.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")
        preview_sql = (
            f'CREATE TABLE IF NOT EXISTS "{db_schema}"."{db_table}" (\n'
            + ",\n".join(cols_sql)
            + "\n);"
        )
        st.code(preview_sql, language="sql")

    # ── STEP 8 (or 7) — Generate Repo ─────────────────────────────────────────
    gen_step = 8 if sel.get("rds") else 7
    st.markdown(
        f'<div class="step-header"><div class="step-num">{gen_step}</div>'
        '<div class="step-title">Generate Repo</div></div>',
        unsafe_allow_html=True,
    )

    # Build helper file assignment list for generators (file objects stripped — just name+dir)
    helper_file_assignments = [
        {"name": e["name"], "dir": e["dir"]}
        for e in all_helper_assignments
    ]

    config = {
        "slug":                slug,
        "pipeline_name":       pipeline_name,
        "aws_region":          aws_region,
        "aws_account_id":      aws_account_id,
        "ecr_repo_name":       ecr_repo_name,
        "stage":               prod_stage,
        "selected":            sel,
        "trigger_type":        trigger_type,
        "schedule_expr":       schedule_expr,
        "sns_topic_arn":       sns_topic_arn,
        "sqs_arn":             sqs_arn,
        "sqs_batch_size":      sqs_batch_size,
        "http_path":           http_path,
        "http_method":         http_method,
        "memory":              memory,
        "timeout":             timeout,
        "architecture":        architecture,
        "python_runtime":      python_runtime,
        "reserved_concurrency": reserved_concurrency,
        "keep_warm":           keep_warm,
        "env_vars":            st.session_state.env_vars,
        "s3_bucket":           s3_bucket,
        "handler_code":        handler_code,
        "requirements_txt":    requirements_txt,
        "create_migration":    create_migration,
        "db_schema":           db_schema,
        "db_table":            db_table,
        "db_columns":          st.session_state.db_columns,
        "helper_file_assignments": helper_file_assignments,
    }

    # File tree preview — group helpers by directory
    helper_lines = ""
    if all_helper_assignments:
        dirs_seen: dict[str, list[str]] = {}
        root_helpers_preview: list[str] = []
        for e in all_helper_assignments:
            d = e["dir"]
            if d:
                dirs_seen.setdefault(d, []).append(e["name"])
            else:
                root_helpers_preview.append(e["name"])
        for fname in root_helpers_preview:
            helper_lines += (
                f'│&nbsp;&nbsp;&nbsp;├── <span class="key">{fname}</span>'
                f' &nbsp;<span class="muted">← helper</span><br>'
            )
        for d, files in sorted(dirs_seen.items()):
            helper_lines += f'│&nbsp;&nbsp;&nbsp;├── <span class="dir">{d}/</span><br>'
            for i, fname in enumerate(files):
                connector = "└──" if i == len(files) - 1 else "├──"
                helper_lines += (
                    f'│&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;{connector} '
                    f'<span class="key">{fname}</span>'
                    f' &nbsp;<span class="muted">← helper</span><br>'
                )
    migration_line = (
        f'├── migrations/<br>'
        f'│&nbsp;&nbsp;&nbsp;└── <span class="key">V001__create_{db_table or "table"}.sql</span><br>'
        if create_migration else ""
    )

    st.markdown(f"""
<div class="file-tree">
<span class="dir">{slug}/</span><br>
├── <span class="key">serverless.yml</span> &nbsp;<span class="muted">← Lambda + triggers + IAM + SNS</span><br>
├── lambda/<br>
│&nbsp;&nbsp;&nbsp;├── <span class="key">handler.py</span><br>
{helper_lines}│&nbsp;&nbsp;&nbsp;└── requirements.txt<br>
├── <span class="key">Dockerfile</span><br>
├── <span class="key">build.sh</span><br>
{migration_line}├── .github/workflows/<br>
│&nbsp;&nbsp;&nbsp;├── <span class="key">1-deploy-ecr.yml</span> &nbsp;<span class="muted">← build + push image (manual)</span><br>
│&nbsp;&nbsp;&nbsp;├── <span class="key">2a-deploy-staging.yml</span> &nbsp;<span class="muted">← manual trigger only</span><br>
│&nbsp;&nbsp;&nbsp;├── <span class="key">2b-deploy-prod.yml</span> &nbsp;<span class="muted">← manual trigger only</span><br>
{"│&nbsp;&nbsp;&nbsp;└── <span class='key'>3-apply-migration.yml</span><br>" if create_migration else ""}└── README.md
</div>
""", unsafe_allow_html=True)

    # File preview tabs
    preview_tabs = st.tabs([
        "serverless.yml", "Dockerfile", "build.sh",
        "GH: ECR", "GH: 2a staging", "GH: 2b prod", "README",
    ])
    with preview_tabs[0]:
        st.code(generate_serverless_yml(config), language="yaml")
    with preview_tabs[1]:
        st.code(generate_dockerfile(config), language="dockerfile")
    with preview_tabs[2]:
        st.code(generate_buildsh(config), language="bash")
    with preview_tabs[3]:
        st.code(generate_github_deploy_ecr(config), language="yaml")
    with preview_tabs[4]:
        st.code(generate_github_deploy_staging(config), language="yaml")
    with preview_tabs[5]:
        st.code(generate_github_deploy_prod(config), language="yaml")
    with preview_tabs[6]:
        st.markdown(generate_readme(config))

    # ── ZIP builder ────────────────────────────────────────────────────────────
    def build_zip(cfg) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            base = cfg["slug"]
            zf.writestr(f"{base}/serverless.yml",           generate_serverless_yml(cfg))
            zf.writestr(f"{base}/lambda/handler.py",        cfg["handler_code"])
            zf.writestr(f"{base}/lambda/requirements.txt",  cfg["requirements_txt"])
            zf.writestr(f"{base}/Dockerfile",               generate_dockerfile(cfg))
            zf.writestr(f"{base}/build.sh",                 generate_buildsh(cfg))
            if cfg["create_migration"]:
                zf.writestr(
                    f"{base}/migrations/V001__create_{cfg['db_table']}.sql",
                    generate_migration_sql(cfg),
                )
            zf.writestr(f"{base}/.github/workflows/1-deploy-ecr.yml",     generate_github_deploy_ecr(cfg))
            zf.writestr(f"{base}/.github/workflows/2a-deploy-staging.yml", generate_github_deploy_staging(cfg))
            zf.writestr(f"{base}/.github/workflows/2b-deploy-prod.yml",    generate_github_deploy_prod(cfg))
            if cfg["create_migration"]:
                zf.writestr(
                    f"{base}/.github/workflows/3-apply-migration.yml",
                    generate_github_apply_migration(cfg),
                )
            zf.writestr(f"{base}/README.md", generate_readme(cfg))
            for e in all_helper_assignments:
                f = e["file"]
                d = e["dir"]
                zip_path = f"{base}/lambda/{d}/{f.name}" if d else f"{base}/lambda/{f.name}"
                f.seek(0)
                zf.writestr(zip_path, f.read())
        buf.seek(0)
        return buf.read()

    st.markdown("<br>", unsafe_allow_html=True)
    zip_bytes = build_zip(config)
    st.download_button(
        label=f"⬇️  Download {slug}/ repo zip",
        data=zip_bytes,
        file_name=f"{slug}.zip",
        mime="application/zip",
        use_container_width=True,
    )

    st.markdown("""
<div class="info-box" style="margin-top:14px;">
<b>Quick start after download:</b><br>
1. &nbsp;<code>IMAGE_TAG=$(git rev-parse --short HEAD) ./build.sh</code> &nbsp;→ push image to ECR<br>
2. &nbsp;<code>npm i -g serverless && sls deploy --stage staging</code> &nbsp;→ deploy staging first<br>
3. &nbsp;<code>sls deploy --stage prod</code> &nbsp;→ deploy prod when staging looks good<br>
4. &nbsp;(if RDS) <code>psql $DB_URL -f migrations/V001__*.sql</code><br><br>
Or push to GitHub and run workflows 1 → 2a → 2b manually from the Actions tab. Nothing deploys automatically.
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CI/CD SETUP GUIDE
# ══════════════════════════════════════════════════════════════════════════════
with tab_cicd:

    st.markdown("""
<div style="font-family:'Syne',sans-serif;font-weight:800;font-size:20px;margin:10px 0 6px;">
  🚀 Setting Up CI/CD on GitHub
</div>
<div style="color:#64748b;font-size:13px;margin-bottom:24px;">
  One-time setup. After this, every push to <code>main</code> auto-deploys to staging,
  then waits for your approval before touching prod.
</div>
""", unsafe_allow_html=True)

    # ── Flow diagram ───────────────────────────────────────────────────────────
    st.markdown("### How the full deploy flow works")
    st.markdown("""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0 28px;">
  <div style="background:#111118;border:1px solid #1e1e2e;border-radius:10px;padding:14px;text-align:center;">
    <div style="font-size:22px;margin-bottom:6px;">1&#xFE0F;&#x20E3;</div>
    <div style="font-weight:700;font-size:12px;color:#e2e8f0;">Push to main</div>
    <div style="color:#64748b;font-size:11px;margin-top:4px;">Engineer merges a PR or pushes a commit</div>
  </div>
  <div style="background:#111118;border:1px solid #7c3aed;border-radius:10px;padding:14px;text-align:center;">
    <div style="font-size:22px;margin-bottom:6px;">2&#xFE0F;&#x20E3;</div>
    <div style="font-weight:700;font-size:12px;color:#e2e8f0;">Build + staging</div>
    <div style="color:#64748b;font-size:11px;margin-top:4px;">Docker → ECR → <code>sls deploy --stage staging</code> → smoke test</div>
  </div>
  <div style="background:#111118;border:1px solid #f59e0b;border-radius:10px;padding:14px;text-align:center;">
    <div style="font-size:22px;margin-bottom:6px;">&#x23F8;&#xFE0F;</div>
    <div style="font-weight:700;font-size:12px;color:#e2e8f0;">Approval gate</div>
    <div style="color:#64748b;font-size:11px;margin-top:4px;">GitHub notifies reviewer — must click Approve to continue</div>
  </div>
  <div style="background:#111118;border:1px solid #10b981;border-radius:10px;padding:14px;text-align:center;">
    <div style="font-size:22px;margin-bottom:6px;">&#x1F680;</div>
    <div style="font-weight:700;font-size:12px;color:#e2e8f0;">Prod deploy</div>
    <div style="color:#64748b;font-size:11px;margin-top:4px;"><code>sls deploy --stage prod</code> runs after approval</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("### Step-by-step setup")

    # Step 1 — OIDC role
    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">1</div>
  <div class="cicd-step-title">Create an IAM Role for GitHub Actions using OIDC (no static AWS keys)</div>
  <div class="cicd-step-body">
    GitHub proves its identity to AWS via OIDC federation. AWS issues short-lived credentials
    per workflow job — no <code>AWS_ACCESS_KEY_ID</code> stored in GitHub at all.
  </div>
</div>
""", unsafe_allow_html=True)

    with st.expander("📋  CloudFormation template — create the OIDC IAM Role (run this once)"):
        st.code(generate_github_oidc_role_cfn(), language="yaml")
        st.markdown("""
<div class="info-box">
Deploy with:<br>
<code>aws cloudformation deploy --template-file oidc-role.yaml --stack-name github-actions-role --capabilities CAPABILITY_IAM --parameter-overrides GitHubOrg=YOUR_ORG GitHubRepo=YOUR_REPO</code><br><br>
Copy the <b>RoleArn</b> from the Outputs — you need it in step 2.
</div>
""", unsafe_allow_html=True)

    # Step 2 — GitHub secret
    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">2</div>
  <div class="cicd-step-title">Add one GitHub Secret</div>
  <div class="cicd-step-body">
    Repo → Settings → Secrets and variables → Actions → New repository secret.
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
| Secret name | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::123456789012:role/GitHubActionsDeployRole` |

That's the only secret. No `AWS_ACCESS_KEY_ID`, no `AWS_SECRET_ACCESS_KEY`.
""")

    # Step 3 — SSM secrets
    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">3</div>
  <div class="cicd-step-title">Store secrets in SSM Parameter Store</div>
  <div class="cicd-step-body">
    Any env var you prefixed with <code>ssm:</code> must exist in SSM before
    <code>sls deploy</code> runs — for both staging and prod paths.
  </div>
</div>
""", unsafe_allow_html=True)

    st.code("""\
# Store for prod
aws ssm put-parameter \\
  --name "/app/prod/db-password" \\
  --value "your-prod-password" \\
  --type SecureString --region eu-west-1

# Store for staging (use a separate value)
aws ssm put-parameter \\
  --name "/app/staging/db-password" \\
  --value "your-staging-password" \\
  --type SecureString --region eu-west-1

# Serverless resolves ${ssm:/app/prod/db-password} at deploy time per stage""",
        language="bash",
    )

    # Step 4 — Push to GitHub
    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">4</div>
  <div class="cicd-step-title">Push the generated repo to GitHub</div>
  <div class="cicd-step-body">
    Unzip the downloaded repo and push it to a new GitHub repo under your org.
  </div>
</div>
""", unsafe_allow_html=True)

    st.code("""\
cd your-pipeline-name/
git init && git add .
git commit -m "feat: initial pipeline scaffold"
git remote add origin git@github.com:YOUR_ORG/your-pipeline-name.git
git push -u origin main""", language="bash")

    # Step 5 — GitHub Environment (approval gate)
    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">5</div>
  <div class="cicd-step-title">Create the "production" GitHub Environment — this is the approval gate</div>
  <div class="cicd-step-body">
    Without this step, workflow 2 would deploy straight to prod with no pause.
    This is what makes it stop and wait for a human.
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
**In GitHub UI:**

1. Repo → **Settings** → **Environments** → **New environment**
2. Name it exactly **`production`** — must match `environment: name: production` in the workflow YAML
3. Enable **Required reviewers** → add yourself or your team leads
4. *(Optional)* Set a **wait timer** — e.g. 5 minutes buffer after staging deploys before the approval request fires
5. *(Optional)* Under **Deployment branches** → add a rule for `main` only — blocks anyone triggering a prod deploy from a feature branch
6. Click **Save protection rules**
""")

    st.markdown("""
<div class="success-box">
After this is set up, the <b>deploy-prod</b> job in workflow 2 will pause at the
<code>environment: production</code> line and GitHub will send an email/notification to
your required reviewers. Nobody touches prod until someone clicks Approve.
</div>
""", unsafe_allow_html=True)

    # Step 6 — First deploy
    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">6</div>
  <div class="cicd-step-title">First deploy — run workflows 1 → 2 → 3 in order</div>
  <div class="cicd-step-body">
    Go to repo → Actions tab. On first deploy run them manually via workflow_dispatch.
    After this, pushes to main trigger everything automatically.
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
| # | Workflow | Trigger | What it does |
|---|---|---|---|
| 1 | **Deploy ECR Image** | Manual only | Builds Docker image → pushes to ECR |
| 2a | **Deploy → staging** | Manual only | Deploys to staging + smoke test |
| 2b | **Deploy → prod** | Manual only | Deploys to prod after staging looks good |
| 3 | **Apply Migration** | Manual only (first deploy or new tables) | Runs `psql` migration against Postgres |
""")

    st.markdown("""
<div class="warn-box">
⚠️ <b>First deploy order matters:</b> 1 → 2 → 3.<br>
Workflow 2 needs the ECR image to already exist before it can deploy the Lambda.<br>
Workflow 3 needs the Lambda deployed first so the DB connection details are available.
</div>
""", unsafe_allow_html=True)

    # Step 7 — Day to day
    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">7</div>
  <div class="cicd-step-title">Day-to-day deploys — fully manual, fully intentional</div>
  <div class="cicd-step-body">
    Push your changes to GitHub, then trigger each workflow manually from the Actions tab.
    No surprises — nothing touches staging or prod unless you kick it off.
  </div>
</div>
""", unsafe_allow_html=True)

    st.code("""\
git add lambda/handler.py
git commit -m "fix: handle null block response"
git push origin main

# Then in GitHub → Actions tab, run in order:
# ① Workflow 1 · Deploy ECR Image     → builds + pushes Docker image (~2 min)
# ② Workflow 2a · Deploy → staging    → sls deploy --stage staging + smoke test (~1 min)
# ③ Check staging looks good
# ④ Workflow 2b · Deploy → prod       → paste the image tag from step ① (~1 min) 🚀""",
        language="bash",
    )

    st.markdown("---")
    st.markdown("### Useful `sls` CLI commands")
    st.code("""\
# Inspect deployed resources
sls info --stage staging
sls info --stage prod

# Test invoke a specific stage
sls invoke --function main --stage staging --log
sls invoke --function main --stage prod --log

# Tail live CloudWatch logs
sls logs --function main --stage staging --tail
sls logs --function main --stage prod --tail

# Dry run — see what would change before deploying
sls deploy --stage prod --noDeploy

# Destroy a stack (careful — this removes the Lambda, schedule, etc.)
sls remove --stage staging
sls remove --stage prod""",
        language="bash",
    )