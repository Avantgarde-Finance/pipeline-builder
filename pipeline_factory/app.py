"""
Pipeline Builder — Serverless Framework Edition (v2)
Component-first approach: pick your AWS building blocks, then configure them.
"""

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

st.set_page_config(
    page_title="Pipeline Builder · Serverless",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;800&display=swap');
:root {
    --bg:#0a0a0f;--surface:#111118;--border:#1e1e2e;--accent:#7c3aed;
    --accent-glow:rgba(124,58,237,0.25);--green:#10b981;--amber:#f59e0b;
    --blue:#3b82f6;--text:#e2e8f0;--muted:#64748b;
}
html,body,[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--text);font-family:'Syne',sans-serif;}
[data-testid="stAppViewContainer"]::before{content:'';position:fixed;top:-40%;left:-20%;width:80vw;height:80vh;background:radial-gradient(ellipse,rgba(124,58,237,0.07) 0%,transparent 70%);pointer-events:none;z-index:0;}
h1,h2,h3{font-family:'Syne',sans-serif!important;}
.top-banner{background:linear-gradient(135deg,rgba(124,58,237,0.15),rgba(16,185,129,0.06));border:1px solid rgba(124,58,237,0.3);border-radius:14px;padding:22px 28px;margin-bottom:28px;}
.step-header{display:flex;align-items:center;gap:14px;margin:32px 0 18px;padding-bottom:12px;border-bottom:1px solid var(--border);}
.step-num{background:var(--accent);color:white;width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:13px;flex-shrink:0;}
.step-title{font-weight:800;font-size:17px;letter-spacing:-0.3px;}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;background:rgba(124,58,237,0.2);color:#a78bfa;border:1px solid rgba(124,58,237,0.3);}
.badge-green{background:rgba(16,185,129,0.15);color:#6ee7b7;border-color:rgba(16,185,129,0.3);}
.badge-amber{background:rgba(245,158,11,0.15);color:#fcd34d;border-color:rgba(245,158,11,0.3);}
.badge-blue{background:rgba(59,130,246,0.15);color:#93c5fd;border-color:rgba(59,130,246,0.3);}
.info-box{background:rgba(124,58,237,0.07);border:1px solid rgba(124,58,237,0.22);border-radius:10px;padding:13px 17px;font-family:'JetBrains Mono',monospace;font-size:12px;color:#c4b5fd;margin:10px 0;}
.warn-box{background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.25);border-radius:10px;padding:13px 17px;font-size:12px;color:#fcd34d;margin:10px 0;}
.success-box{background:rgba(16,185,129,0.07);border:1px solid rgba(16,185,129,0.25);border-radius:10px;padding:13px 17px;font-size:12px;color:#6ee7b7;margin:10px 0;}
.file-chip{display:inline-flex;align-items:center;gap:6px;background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);border-radius:6px;padding:4px 10px;font-family:'JetBrains Mono',monospace;font-size:11px;color:#93c5fd;margin:3px;}
.file-tree{background:#0d0d14;border:1px solid var(--border);border-radius:10px;padding:16px 20px;font-family:'JetBrains Mono',monospace;font-size:12px;line-height:2;color:var(--text);}
.file-tree .dir{color:#7c3aed;font-weight:700;}
.file-tree .key{color:#10b981;}
.file-tree .muted{color:var(--muted);font-size:11px;}
.cicd-step{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 20px 16px 52px;margin:8px 0;position:relative;}
.cicd-step-num{position:absolute;left:16px;top:16px;background:var(--accent);color:white;width:24px;height:24px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;}
.cicd-step-title{font-weight:700;font-size:14px;margin-bottom:6px;}
.cicd-step-body{font-size:13px;color:#94a3b8;line-height:1.6;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div>div{background:var(--surface)!important;border:1px solid var(--border)!important;color:var(--text)!important;border-radius:8px!important;font-family:'JetBrains Mono',monospace!important;font-size:13px!important;}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{border-color:var(--accent)!important;box-shadow:0 0 0 3px var(--accent-glow)!important;}
.stButton>button{background:var(--accent)!important;color:white!important;border:none!important;border-radius:8px!important;font-family:'Syne',sans-serif!important;font-weight:700!important;font-size:13px!important;padding:9px 20px!important;transition:all 0.15s!important;}
.stButton>button:hover{background:#6d28d9!important;transform:translateY(-1px)!important;}
.stCheckbox>label{color:var(--text)!important;font-size:13px!important;}
.stSelectbox label,.stTextInput label,.stTextArea label,.stSlider label,.stNumberInput label{color:var(--muted)!important;font-size:11px!important;font-family:'JetBrains Mono',monospace!important;text-transform:uppercase!important;letter-spacing:0.5px!important;}
div[data-testid="stExpander"]{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:10px!important;}
[data-testid="stTabs"] button{font-family:'JetBrains Mono',monospace!important;font-size:12px!important;color:var(--muted)!important;}
[data-testid="stTabs"] button[aria-selected="true"]{color:var(--accent)!important;border-bottom-color:var(--accent)!important;}
.stDownloadButton>button{background:linear-gradient(135deg,#10b981,#059669)!important;color:white!important;border:none!important;border-radius:10px!important;font-family:'Syne',sans-serif!important;font-weight:800!important;font-size:15px!important;padding:14px 32px!important;width:100%!important;box-shadow:0 4px 24px rgba(16,185,129,0.3)!important;}
hr{border-color:var(--border)!important;}
</style>
""", unsafe_allow_html=True)

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

tab_build, tab_cicd = st.tabs(["🔧  Build Pipeline", "🚀  CI/CD Setup Guide"])

if "env_vars" not in st.session_state:
    st.session_state.env_vars = []
if "db_columns" not in st.session_state:
    st.session_state.db_columns = [
        {"name": "id",         "type": "BIGSERIAL",   "pk": True,  "nullable": False, "default": ""},
        {"name": "created_at", "type": "TIMESTAMPTZ", "pk": False, "nullable": False, "default": "NOW()"},
    ]
if "sel" not in st.session_state:
    st.session_state.sel = {}

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BUILD PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
with tab_build:

    # STEP 1 — Component Picker
    st.markdown('<div class="step-header"><div class="step-num">1</div><div class="step-title">Choose Your Pipeline Components</div></div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#64748b;font-size:13px;margin-bottom:16px;">Select the AWS services you want in this pipeline. Lambda is always included as the compute layer.</div>', unsafe_allow_html=True)

    COMPONENTS = [
        {"key": "lambda",        "icon": "λ",   "name": "Lambda",          "desc": "Python compute. Always included.",                          "required": True},
        {"key": "eventbridge",   "icon": "⏰",  "name": "EventBridge",     "desc": "Schedule trigger (rate or cron)",                           "required": False},
        {"key": "sns_trigger",   "icon": "📣",  "name": "SNS Trigger",     "desc": "Subscribe Lambda to an existing SNS topic",                 "required": False},
        {"key": "sns_publisher", "icon": "📤",  "name": "SNS Publisher",   "desc": "Create staging + prod SNS topics, Lambda publishes to them", "required": False},
        {"key": "sqs",           "icon": "📬",  "name": "SQS Queue",       "desc": "Queue trigger + batch processing",                          "required": False},
        {"key": "api_gateway",   "icon": "🌐",  "name": "API Gateway",     "desc": "HTTP endpoint (HTTP API v2)",                               "required": False},
        {"key": "sns_failure",   "icon": "🚨",  "name": "Failure Alerts",  "desc": "SNS topic for failed invocations",                          "required": False},
        {"key": "rds",           "icon": "🗄️", "name": "Postgres / RDS",  "desc": "Target table + migration SQL",                              "required": False},
        {"key": "s3",            "icon": "🪣",  "name": "S3",              "desc": "S3 read/write + IAM policy",                                "required": False},
        {"key": "xray",          "icon": "🔍",  "name": "X-Ray Tracing",   "desc": "Distributed tracing for Lambda",                            "required": False},
    ]

    sel = {}
    cols = st.columns(3)
    for i, comp in enumerate(COMPONENTS):
        with cols[i % 3]:
            if comp["required"]:
                st.checkbox(f"{comp['icon']}  **{comp['name']}** — *{comp['desc']}*", value=True, disabled=True, key=f"comp_req_{comp['key']}")
                sel[comp["key"]] = True
            else:
                default = st.session_state.sel.get(comp["key"], False)
                val = st.checkbox(f"{comp['icon']}  **{comp['name']}** — *{comp['desc']}*", value=default, key=f"comp_{comp['key']}")
                sel[comp["key"]] = val

    st.session_state.sel = sel
    selected_names = [c["name"] for c in COMPONENTS if sel.get(c["key"])]
    chips = "".join([f'<span class="badge" style="margin:2px;">{n}</span>' for n in selected_names])
    st.markdown(f'<div style="margin-top:8px;"><span style="color:#64748b;font-size:11px;font-family:\'JetBrains Mono\',monospace;text-transform:uppercase;letter-spacing:0.5px;">Pipeline includes:</span> {chips}</div>', unsafe_allow_html=True)

    # STEP 2 — Pipeline Identity
    st.markdown('<div class="step-header"><div class="step-num">2</div><div class="step-title">Pipeline Identity</div></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 1.5, 1])
    with c1:
        pipeline_name = st.text_input("Pipeline name", value="arbitrum-block-fetcher")
        slug = re.sub(r"[^a-z0-9-]", "-", pipeline_name.lower()).strip("-") or "my-pipeline"
    with c2:
        aws_region = st.selectbox("AWS Region", ["eu-west-1", "us-east-1", "us-west-2", "ap-southeast-1", "ap-northeast-1"])
    with c3:
        prod_stage = st.selectbox("Prod stage name", ["prod", "production", "main"])

    c1, c2 = st.columns(2)
    with c1: aws_account_id = st.text_input("AWS Account ID", value="289390447514")
    with c2: ecr_repo_name  = st.text_input("ECR Repository name", value=slug)

    # STEP 3 — Configure Triggers & Publishers
    trigger_type      = "none"
    schedule_expr     = ""
    sns_topic_arn     = ""
    sns_publisher_base    = ""
    sns_publisher_suffix_staging = "_stg"
    sns_publisher_suffix_prod    = ""
    sqs_arn           = ""
    sqs_batch_size    = 10
    http_path         = "/run"
    http_method       = "GET"

    has_config = any(sel.get(k) for k in ["eventbridge", "sns_trigger", "sns_publisher", "sqs", "api_gateway"])
    if has_config:
        st.markdown('<div class="step-header"><div class="step-num">3</div><div class="step-title">Configure Trigger(s) & Publishers</div></div>', unsafe_allow_html=True)

        if sel.get("eventbridge"):
            st.markdown("##### ⏰ EventBridge Schedule")
            trigger_type = "schedule"
            c1, c2 = st.columns([1, 2])
            with c1:
                schedule_mode = st.radio("Mode", ["Rate", "Cron"], horizontal=True)
            with c2:
                if schedule_mode == "Rate":
                    r1, r2 = st.columns(2)
                    with r1: rate_val  = st.number_input("Every N", min_value=1, value=1)
                    with r2: rate_unit = st.selectbox("Unit", ["hour", "hours", "day", "days", "minute", "minutes"])
                    schedule_expr = f"rate({rate_val} {rate_unit})"
                else:
                    c1b, c2b, c3b, c4b, c5b = st.columns(5)
                    with c1b: m   = st.text_input("Min",  "0")
                    with c2b: h   = st.text_input("Hour", "2")
                    with c3b: dom = st.text_input("DoM",  "*")
                    with c4b: mon = st.text_input("Mon",  "*")
                    with c5b: dow = st.text_input("DoW",  "?")
                    schedule_expr = f"cron({m} {h} {dom} {mon} {dow} *)"
            st.markdown(f'<div class="info-box">serverless.yml event: <b>schedule: {schedule_expr}</b></div>', unsafe_allow_html=True)

        if sel.get("sns_trigger"):
            st.markdown("##### 📣 SNS Trigger — subscribe to an existing topic")
            if trigger_type == "none":
                trigger_type = "sns"
            sns_topic_arn = st.text_input(
                "Existing SNS Topic ARN",
                value=f"arn:aws:sns:{aws_region}:{aws_account_id}:my-existing-topic",
                help="Lambda subscribes to this topic. Same ARN used for all stages.",
            )
            st.markdown('<div class="info-box">The topic already exists — Serverless just wires up the subscription.</div>', unsafe_allow_html=True)

        if sel.get("sns_publisher"):
            st.markdown("##### 📤 SNS Publisher — create staging + prod topics, Lambda publishes to them")
            c1, c2, c3 = st.columns([3, 1.5, 1.5])
            with c1:
                sns_publisher_base = st.text_input(
                    "Base topic name",
                    value="my-pipeline-events",
                    help="Serverless creates {base}{suffix} for each stage",
                )
            with c2:
                sns_publisher_suffix_staging = st.text_input(
                    "Staging suffix",
                    value="_stg",
                    help="e.g. my-pipeline-events_stg",
                )
            with c3:
                sns_publisher_suffix_prod = st.text_input(
                    "Prod suffix",
                    value="",
                    help="Usually empty — e.g. my-pipeline-events",
                )

            staging_topic = f"{sns_publisher_base}{sns_publisher_suffix_staging}"
            prod_topic    = f"{sns_publisher_base}{sns_publisher_suffix_prod}" if sns_publisher_suffix_prod else sns_publisher_base
            st.markdown(f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0;">
  <div class="info-box">
    <span style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;">Staging creates</span><br>
    <b>{staging_topic}</b>
  </div>
  <div class="info-box" style="background:rgba(16,185,129,0.07);border-color:rgba(16,185,129,0.25);color:#6ee7b7;">
    <span style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;">Prod creates</span><br>
    <b>{prod_topic}</b>
  </div>
</div>
<div class="info-box">Serverless creates the topic for each stage and injects <code>SNS_TOPIC_ARN</code> as an env var so the Lambda knows where to publish.</div>
""", unsafe_allow_html=True)

        if sel.get("sqs"):
            st.markdown("##### 📬 SQS Queue")
            if trigger_type == "none": trigger_type = "sqs"
            c1, c2 = st.columns(2)
            with c1: sqs_arn        = st.text_input("SQS Queue ARN", f"arn:aws:sqs:{aws_region}:{aws_account_id}:my-queue")
            with c2: sqs_batch_size = st.number_input("Batch size", 1, 10000, 10)

        if sel.get("api_gateway"):
            st.markdown("##### 🌐 API Gateway")
            if trigger_type == "none": trigger_type = "http"
            c1, c2 = st.columns(2)
            with c1: http_path   = st.text_input("Path", "/run")
            with c2: http_method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])

    # STEP 4 — Lambda Config
    st.markdown('<div class="step-header"><div class="step-num">4</div><div class="step-title">Lambda Configuration</div></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: memory       = st.select_slider("Memory (MB)", options=[128, 256, 512, 1024, 2048, 3008, 4096, 8192, 10240], value=256)
    with c2: timeout      = st.slider("Timeout (seconds)", 10, 900, 300)
    with c3: architecture = st.selectbox("Architecture", ["x86_64", "arm64"])

    c1, c2 = st.columns(2)
    with c1: python_runtime       = st.selectbox("Python version", ["python3.12", "python3.11", "python3.10"])
    with c2: reserved_concurrency = st.number_input("Reserved concurrency (-1 = unreserved)", min_value=-1, value=-1)
    keep_warm = st.checkbox("Provisioned concurrency (keep warm)", value=False)

    # STEP 5 — Environment Variables
    st.markdown('<div class="step-header"><div class="step-num">5</div><div class="step-title">Environment Variables</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">Prefix values with <b>ssm:</b> to resolve from SSM Parameter Store at deploy time — secrets never touch the repo.<br>e.g. <code>DB_PASSWORD</code> → <code>ssm:/app/prod/db-password</code></div>', unsafe_allow_html=True)

    if st.button("＋ Add variable", key="add_env"):
        st.session_state.env_vars.append({"key": "", "value": ""})

    for i, ev in enumerate(st.session_state.env_vars):
        c1, c2, c3 = st.columns([2, 3, 0.4])
        with c1:
            st.session_state.env_vars[i]["key"] = st.text_input("Key", ev["key"], key=f"ek_{i}")
        with c2:
            val = st.text_input("Value", ev["value"], key=f"ev_{i}")
            st.session_state.env_vars[i]["value"] = val
            if val.startswith("ssm:"): st.markdown('<span class="badge-amber badge">SSM secret</span>', unsafe_allow_html=True)
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✕", key=f"rm_{i}"):
                st.session_state.env_vars.pop(i)
                st.rerun()

    s3_bucket = ""
    if sel.get("s3"):
        s3_bucket = st.text_input("S3 bucket name (added to IAM policy)", "my-pipeline-bucket")

    # STEP 6 — Lambda Code & Helper Files
    st.markdown('<div class="step-header"><div class="step-num">6</div><div class="step-title">Lambda Code & Helper Files</div></div>', unsafe_allow_html=True)

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

    handler_code     = st.text_area("handler.py", default_handler, height=260)
    requirements_txt = st.text_area("requirements.txt", "web3>=6.0.0\npsycopg2-binary>=2.9.9\nboto3>=1.34.0\nrequests>=2.31.0\n", height=110)

    st.markdown("#### 📎 Helper Files")
    st.markdown('<div class="info-box">Upload any additional Python modules, config files, or scripts. These land in <code>lambda/</code> alongside <code>handler.py</code> and are built into the Docker image — import them with <code>from db import get_connection</code>.</div>', unsafe_allow_html=True)

    uploaded_helpers = st.file_uploader(
        "Upload helper files (e.g. db.py, utils.py, config.json, abi.json, queries.sql)",
        accept_multiple_files=True,
        type=["py", "json", "yaml", "yml", "env", "sql", "txt", "sh"],
        key="helper_files",
    )

    if uploaded_helpers:
        chips_html = "".join([f'<span class="file-chip">📄 lambda/{f.name}</span>' for f in uploaded_helpers])
        st.markdown(f'<div style="margin:8px 0;">{chips_html}</div>', unsafe_allow_html=True)
        st.markdown('<div class="success-box">✅ These will be copied into <code>lambda/</code> in the generated repo and built into the Docker image.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#64748b;font-size:12px;font-family:\'JetBrains Mono\',monospace;margin:6px 0;">No helper files added — only handler.py and requirements.txt will be in lambda/</div>', unsafe_allow_html=True)

    # STEP 7 — RDS / Postgres
    db_schema = db_table = ""
    create_migration = False

    if sel.get("rds"):
        st.markdown('<div class="step-header"><div class="step-num">7</div><div class="step-title">Postgres / RDS — Target Table</div></div>', unsafe_allow_html=True)
        create_migration = True

        c1, c2 = st.columns(2)
        with c1: db_schema = st.text_input("Schema", "public")
        with c2: db_table  = st.text_input("Table name", slug.replace("-", "_"))

        st.markdown("**Table columns**")
        if st.button("＋ Add column", key="add_col"):
            st.session_state.db_columns.append({"name": "", "type": "TEXT", "pk": False, "nullable": True, "default": ""})

        pg_types = ["TEXT", "INTEGER", "BIGINT", "BIGSERIAL", "NUMERIC", "BOOLEAN", "TIMESTAMPTZ", "TIMESTAMP", "JSONB", "UUID", "VARCHAR(255)"]

        for i, col in enumerate(st.session_state.db_columns):
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 0.7, 0.7, 2, 0.4])
            with c1: st.session_state.db_columns[i]["name"]     = st.text_input("Column",  col["name"],    key=f"cn_{i}")
            with c2: st.session_state.db_columns[i]["type"]     = st.selectbox("Type", pg_types, index=pg_types.index(col["type"]) if col["type"] in pg_types else 0, key=f"ct_{i}")
            with c3: st.session_state.db_columns[i]["pk"]       = st.checkbox("PK",   col["pk"],       key=f"cpk_{i}")
            with c4: st.session_state.db_columns[i]["nullable"] = st.checkbox("NULL", col["nullable"],  key=f"cnull_{i}")
            with c5: st.session_state.db_columns[i]["default"]  = st.text_input("Default", col["default"], key=f"cdef_{i}")
            with c6:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✕", key=f"rmc_{i}"):
                    st.session_state.db_columns.pop(i)
                    st.rerun()

        cols_sql, pk_cols = [], []
        for col in st.session_state.db_columns:
            if not col["name"]: continue
            parts = [f'    "{col["name"]}"', col["type"]]
            if col["pk"]: pk_cols.append(f'"{col["name"]}"')
            if not col["nullable"] and not col["pk"]: parts.append("NOT NULL")
            if col["default"]: parts.append(f"DEFAULT {col['default']}")
            cols_sql.append(" ".join(parts))
        if pk_cols: cols_sql.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")
        preview_sql = f'CREATE TABLE IF NOT EXISTS "{db_schema}"."{db_table}" (\n' + ",\n".join(cols_sql) + "\n);"
        st.code(preview_sql, language="sql")

    # STEP Generate
    gen_step = 8 if sel.get("rds") else 7
    st.markdown(f'<div class="step-header"><div class="step-num">{gen_step}</div><div class="step-title">Generate Repo</div></div>', unsafe_allow_html=True)

    config = {
        "slug":                       slug,
        "pipeline_name":              pipeline_name,
        "aws_region":                 aws_region,
        "aws_account_id":             aws_account_id,
        "ecr_repo_name":              ecr_repo_name,
        "stage":                      prod_stage,
        "selected":                   sel,
        "trigger_type":               trigger_type,
        "schedule_expr":              schedule_expr,
        "sns_topic_arn":              sns_topic_arn,
        "sns_publisher_base":         sns_publisher_base,
        "sns_publisher_suffix_staging": sns_publisher_suffix_staging,
        "sns_publisher_suffix_prod":  sns_publisher_suffix_prod,
        "sqs_arn":                    sqs_arn,
        "sqs_batch_size":             sqs_batch_size,
        "http_path":                  http_path,
        "http_method":                http_method,
        "memory":                     memory,
        "timeout":                    timeout,
        "architecture":               architecture,
        "python_runtime":             python_runtime,
        "reserved_concurrency":       reserved_concurrency,
        "keep_warm":                  keep_warm,
        "env_vars":                   st.session_state.env_vars,
        "s3_bucket":                  s3_bucket,
        "handler_code":               handler_code,
        "requirements_txt":           requirements_txt,
        "create_migration":           create_migration,
        "db_schema":                  db_schema,
        "db_table":                   db_table,
        "db_columns":                 st.session_state.db_columns,
    }

    helper_lines = "".join([f'│&nbsp;&nbsp;&nbsp;├── <span class="key">{f.name}</span> &nbsp;<span class="muted">← helper</span><br>' for f in (uploaded_helpers or [])])
    migration_line = f'├── migrations/<br>│&nbsp;&nbsp;&nbsp;└── <span class="key">V001__create_{db_table or "table"}.sql</span><br>' if create_migration else ""

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
│&nbsp;&nbsp;&nbsp;├── <span class="key">1-deploy-ecr.yml</span> &nbsp;<span class="muted">← build + push image</span><br>
│&nbsp;&nbsp;&nbsp;├── <span class="key">2a-deploy-staging.yml</span> &nbsp;<span class="muted">← auto on push to main</span><br>
│&nbsp;&nbsp;&nbsp;├── <span class="key">2b-deploy-prod.yml</span> &nbsp;<span class="muted">← manual trigger only</span><br>
{"│&nbsp;&nbsp;&nbsp;└── <span class='key'>3-apply-migration.yml</span><br>" if create_migration else ""}└── README.md
</div>
""", unsafe_allow_html=True)

    preview_tabs = st.tabs(["serverless.yml", "Dockerfile", "build.sh", "GH: ECR", "GH: 2a staging", "GH: 2b prod", "README"])
    with preview_tabs[0]: st.code(generate_serverless_yml(config), language="yaml")
    with preview_tabs[1]: st.code(generate_dockerfile(config), language="dockerfile")
    with preview_tabs[2]: st.code(generate_buildsh(config), language="bash")
    with preview_tabs[3]: st.code(generate_github_deploy_ecr(config), language="yaml")
    with preview_tabs[4]: st.code(generate_github_deploy_staging(config), language="yaml")
    with preview_tabs[5]: st.code(generate_github_deploy_prod(config), language="yaml")
    with preview_tabs[6]: st.markdown(generate_readme(config))

    def build_zip(cfg) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            base = cfg["slug"]
            zf.writestr(f"{base}/serverless.yml",            generate_serverless_yml(cfg))
            zf.writestr(f"{base}/lambda/handler.py",         cfg["handler_code"])
            zf.writestr(f"{base}/lambda/requirements.txt",   cfg["requirements_txt"])
            zf.writestr(f"{base}/Dockerfile",                generate_dockerfile(cfg))
            zf.writestr(f"{base}/build.sh",                  generate_buildsh(cfg))
            if cfg["create_migration"]:
                zf.writestr(f"{base}/migrations/V001__create_{cfg['db_table']}.sql", generate_migration_sql(cfg))
            zf.writestr(f"{base}/.github/workflows/1-deploy-ecr.yml",     generate_github_deploy_ecr(cfg))
            zf.writestr(f"{base}/.github/workflows/2a-deploy-staging.yml", generate_github_deploy_staging(cfg))
            zf.writestr(f"{base}/.github/workflows/2b-deploy-prod.yml",    generate_github_deploy_prod(cfg))
            if cfg["create_migration"]:
                zf.writestr(f"{base}/.github/workflows/3-apply-migration.yml", generate_github_apply_migration(cfg))
            zf.writestr(f"{base}/README.md", generate_readme(cfg))
            for f in (uploaded_helpers or []):
                f.seek(0)
                zf.writestr(f"{base}/lambda/{f.name}", f.read())
        buf.seek(0)
        return buf.read()

    st.markdown("<br>", unsafe_allow_html=True)
    zip_bytes = build_zip(config)
    st.download_button(label=f"⬇️  Download {slug}/ repo zip", data=zip_bytes, file_name=f"{slug}.zip", mime="application/zip", use_container_width=True)
    st.markdown("""<div class="info-box" style="margin-top:14px;">
<b>Quick start after download:</b><br>
1. &nbsp;Run workflow <b>1 · Deploy ECR Image</b> from GitHub Actions<br>
2. &nbsp;Run workflow <b>2a · Deploy → staging</b><br>
3. &nbsp;Run workflow <b>2b · Deploy → prod</b> (manual, paste image tag from step 1)<br>
4. &nbsp;(if RDS) Run workflow <b>3 · Apply Migration</b>
</div>""", unsafe_allow_html=True)


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
    <div style="color:#64748b;font-size:11px;margin-top:4px;">Docker → ECR → <code>sls deploy --stage staging</code></div>
  </div>
  <div style="background:#111118;border:1px solid #f59e0b;border-radius:10px;padding:14px;text-align:center;">
    <div style="font-size:22px;margin-bottom:6px;">&#x23F8;&#xFE0F;</div>
    <div style="font-weight:700;font-size:12px;color:#e2e8f0;">Manual gate</div>
    <div style="color:#64748b;font-size:11px;margin-top:4px;">Run 2b manually when staging looks good</div>
  </div>
  <div style="background:#111118;border:1px solid #10b981;border-radius:10px;padding:14px;text-align:center;">
    <div style="font-size:22px;margin-bottom:6px;">&#x1F680;</div>
    <div style="font-weight:700;font-size:12px;color:#e2e8f0;">Prod deploy</div>
    <div style="color:#64748b;font-size:11px;margin-top:4px;"><code>sls deploy --stage prod</code> runs</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("### Step-by-step setup")

    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">1</div>
  <div class="cicd-step-title">Create an IAM Role for GitHub Actions using OIDC (no static AWS keys)</div>
  <div class="cicd-step-body">GitHub proves its identity to AWS via OIDC federation. AWS issues short-lived credentials per workflow job — no <code>AWS_ACCESS_KEY_ID</code> stored in GitHub at all.</div>
</div>
""", unsafe_allow_html=True)

    with st.expander("📋  CloudFormation template — create the OIDC IAM Role (run this once)"):
        st.code(generate_github_oidc_role_cfn(), language="yaml")
        st.markdown("""<div class="info-box">
Deploy with:<br>
<code>aws cloudformation deploy --template-file oidc-role.yaml --stack-name github-actions-role --capabilities CAPABILITY_IAM --parameter-overrides GitHubOrg=YOUR_ORG GitHubRepo=YOUR_REPO</code><br><br>
Copy the <b>RoleArn</b> from the Outputs — you need it in step 2.
</div>""", unsafe_allow_html=True)

    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">2</div>
  <div class="cicd-step-title">Add one GitHub Secret</div>
  <div class="cicd-step-body">Repo → Settings → Secrets and variables → Actions → New repository secret.</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
| Secret name | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::123456789012:role/GitHubActionsDeployRole` |

That's the only secret. No `AWS_ACCESS_KEY_ID`, no `AWS_SECRET_ACCESS_KEY`.
""")

    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">3</div>
  <div class="cicd-step-title">Store secrets in SSM Parameter Store</div>
  <div class="cicd-step-body">Any env var prefixed with <code>ssm:</code> must exist in SSM before <code>sls deploy</code> runs — for both staging and prod paths.</div>
</div>
""", unsafe_allow_html=True)

    st.code("""\
# Store for prod
aws ssm put-parameter \\
  --name "/app/prod/db-password" \\
  --value "your-prod-password" \\
  --type SecureString --region eu-west-1

# Store for staging
aws ssm put-parameter \\
  --name "/app/staging/db-password" \\
  --value "your-staging-password" \\
  --type SecureString --region eu-west-1

# Serverless resolves ${ssm:/app/prod/db-password} at deploy time per stage""", language="bash")

    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">4</div>
  <div class="cicd-step-title">Push the generated repo to GitHub</div>
  <div class="cicd-step-body">Unzip the downloaded repo and push it to a new GitHub repo under your org.</div>
</div>
""", unsafe_allow_html=True)

    st.code("""\
cd your-pipeline-name/
git init && git add .
git commit -m "feat: initial pipeline scaffold"
git remote add origin git@github.com:YOUR_ORG/your-pipeline-name.git
git push -u origin main""", language="bash")

    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">5</div>
  <div class="cicd-step-title">First deploy — run workflows 1 → 2a → 2b in order</div>
  <div class="cicd-step-body">Go to repo → Actions tab. On first deploy run them manually via workflow_dispatch. After this, pushes to main trigger 1 and 2a automatically.</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
| # | Workflow | Trigger | What it does |
|---|---|---|---|
| 1 | **Deploy ECR Image** | Push to `main` (lambda/ or Dockerfile changed) | Builds Docker image → pushes to ECR |
| 2a | **Deploy → staging** | Push to `main` (any file) | Auto-deploys staging |
| 2b | **Deploy → prod** | Manual only | Paste image tag from workflow 1 → deploys prod |
| 3 | **Apply Migration** | Manual only (first deploy or new tables) | Runs `psql` migration against Postgres |
""")

    st.markdown("""<div class="warn-box">
⚠️ <b>First deploy order matters:</b> 1 → 2a → 2b → 3.<br>
Workflow 2a needs the ECR image to already exist before it can deploy the Lambda.
</div>""", unsafe_allow_html=True)

    st.markdown("""
<div class="cicd-step">
  <div class="cicd-step-num">6</div>
  <div class="cicd-step-title">Day-to-day deploys — the full automated flow</div>
  <div class="cicd-step-body">Push to main. Staging deploys automatically via 2a. Run 2b manually when you're ready to promote to prod.</div>
</div>
""", unsafe_allow_html=True)

    st.code("""\
git add lambda/handler.py
git commit -m "fix: handle null block response"
git push origin main

# What happens automatically:
# ① Docker image built + pushed to ECR             (~2 min)
# ② sls deploy --stage staging                     (~1 min)
# ③ ⏸  Check staging looks good
# ④ Go to Actions → run 2b manually → sls deploy --stage prod  🚀""", language="bash")

    st.markdown("---")
    st.markdown("### IAM inline policy — `ServerlessDeployPolicy`")
    st.markdown("Add this to your `GitHubActionsDeployRole`:")

    st.code("""\
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*", "events:*", "scheduler:*", "sns:*", "sqs:*",
        "apigateway:*", "xray:*", "cloudformation:*", "logs:*",
        "secretsmanager:GetSecretValue",
        "ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath",
        "iam:GetRole", "iam:CreateRole", "iam:DeleteRole",
        "iam:AttachRolePolicy", "iam:DetachRolePolicy",
        "iam:PutRolePolicy", "iam:DeleteRolePolicy",
        "iam:TagRole", "iam:UntagRole", "iam:GetRolePolicy",
        "iam:ListRolePolicies", "iam:ListAttachedRolePolicies",
        "ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage",
        "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload", "ecr:PutImage",
        "ecr:CreateRepository", "ecr:SetRepositoryPolicy"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["ecr:DeleteRepository", "ecr:DescribeRepositories", "ecr:ListImages"],
      "Resource": "arn:aws:ecr:eu-west-1:289390447514:repository/*"
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::289390447514:role/*",
      "Condition": {
        "StringEquals": {"iam:PassedToService": "lambda.amazonaws.com"}
      }
    }
  ]
}""", language="json")

    st.markdown("---")
    st.markdown("### Secrets Manager — DB credentials pattern")
    st.markdown("""
| Secret name | Keys |
|---|---|
| `your-pipeline/staging/creds` | `db_host`, `db_port`, `db_name`, `db_user`, `db_password` |
| `your-pipeline/prod/creds` | `db_host`, `db_port`, `db_name`, `db_user`, `db_password` |
""")

    st.markdown("---")
    st.markdown("### Useful `sls` CLI commands")
    st.code("""\
sls info --stage staging
sls info --stage prod
sls invoke --function main --stage staging --log
sls invoke --function main --stage prod --log
sls logs --function main --stage staging --tail
sls logs --function main --stage prod --tail
sls deploy --stage prod --noDeploy
sls remove --stage staging
sls remove --stage prod""", language="bash")