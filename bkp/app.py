"""
Pipeline Builder — Streamlit UI to scaffold and generate deployable AWS pipeline repos.
"""

import io
import json
import re
import textwrap
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Pipeline Builder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Theme / CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;800&display=swap');

:root {
    --bg:      #0a0c10;
    --bg2:     #10141c;
    --bg3:     #181e2a;
    --border:  #1e2a3a;
    --accent:  #00d4ff;
    --accent2: #7c3aed;
    --green:   #10b981;
    --amber:   #f59e0b;
    --red:     #ef4444;
    --text:    #e2e8f0;
    --muted:   #64748b;
    --mono:    'JetBrains Mono', monospace;
    --sans:    'Syne', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Inputs */
input, textarea, select, [data-baseweb="input"] input,
[data-baseweb="textarea"] textarea, [data-baseweb="select"] div {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 13px !important;
}
input:focus, textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
    outline: none !important;
}

/* Buttons */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: var(--mono) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    border-radius: 4px !important;
    letter-spacing: 0.05em !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: var(--accent) !important;
    color: var(--bg) !important;
}

/* Primary button */
.stButton > button[kind="primary"],
div[data-testid="stFormSubmitButton"] > button {
    background: var(--accent) !important;
    color: var(--bg) !important;
    border: none !important;
    font-weight: 700 !important;
}
.stButton > button[kind="primary"]:hover {
    background: #00b8d9 !important;
}

/* Download button */
.stDownloadButton > button {
    background: var(--green) !important;
    border: none !important;
    color: #000 !important;
    font-family: var(--mono) !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    padding: 12px 28px !important;
    border-radius: 4px !important;
    letter-spacing: 0.05em !important;
    width: 100% !important;
}

/* Selectbox */
[data-baseweb="select"] {
    background: var(--bg3) !important;
}
[data-baseweb="popover"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
}

/* Slider */
[data-baseweb="slider"] [role="slider"] {
    background: var(--accent) !important;
}

/* Checkbox */
[data-testid="stCheckbox"] label { font-family: var(--mono) !important; font-size: 13px !important; }

/* Expander */
[data-testid="stExpander"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* Tabs */
[data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid var(--border) !important; }
[data-baseweb="tab"] { font-family: var(--mono) !important; font-size: 13px !important; }
[aria-selected="true"][data-baseweb="tab"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }

/* Alerts */
[data-testid="stSuccess"] { background: rgba(16,185,129,0.1) !important; border: 1px solid var(--green) !important; border-radius: 6px !important; }
[data-testid="stInfo"]    { background: rgba(0,212,255,0.08) !important; border: 1px solid var(--accent) !important; border-radius: 6px !important; }
[data-testid="stWarning"] { background: rgba(245,158,11,0.1) !important; border: 1px solid var(--amber) !important; border-radius: 6px !important; }

/* Code */
code, pre { font-family: var(--mono) !important; background: var(--bg3) !important; border-radius: 4px !important; }

/* Labels */
label, .stSelectbox label, .stTextInput label, .stTextArea label, .stSlider label, .stCheckbox label {
    font-family: var(--mono) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: var(--muted) !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

/* Radio */
[data-testid="stRadio"] label { font-family: var(--mono) !important; font-size: 13px !important; text-transform: none !important; letter-spacing: 0 !important; color: var(--text) !important; }

/* Metric */
[data-testid="stMetric"] { background: var(--bg2) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; padding: 12px !important; }

/* Number input */
[data-testid="stNumberInput"] input { font-family: var(--mono) !important; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--bg3) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 8px !important;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─── Custom components ─────────────────────────────────────────────────────────

def badge(text, color="#00d4ff"):
    return f'<span style="background:rgba(0,212,255,0.1);border:1px solid {color};color:{color};font-family:JetBrains Mono,monospace;font-size:11px;font-weight:600;padding:2px 10px;border-radius:3px;letter-spacing:0.06em">{text}</span>'

def section_header(title, subtitle=None):
    st.markdown(f"""
    <div style="margin-bottom:24px">
        <h2 style="font-family:Syne,sans-serif;font-size:22px;font-weight:800;
                   color:#e2e8f0;margin:0 0 4px 0;letter-spacing:-0.02em">{title}</h2>
        {'<p style="font-family:JetBrains Mono,monospace;font-size:13px;color:#64748b;margin:0">' + subtitle + '</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def file_preview(filename, content, lang="python"):
    st.markdown(f"""
    <div style="background:#10141c;border:1px solid #1e2a3a;border-radius:8px;margin-bottom:12px">
        <div style="padding:8px 14px;border-bottom:1px solid #1e2a3a;display:flex;align-items:center;gap:8px">
            <span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#00d4ff;font-weight:600">{filename}</span>
        </div>
        <pre style="margin:0;padding:14px;font-family:JetBrains Mono,monospace;
                    font-size:12px;color:#94a3b8;overflow-x:auto;white-space:pre">{content[:1200]}{'...' if len(content)>1200 else ''}</pre>
    </div>
    """, unsafe_allow_html=True)

def step_pill(num, label, active=False, done=False):
    if done:
        col, lbl = "#10b981", "✓"
        bg = "rgba(16,185,129,0.1)"
        border = "#10b981"
    elif active:
        col, lbl = "#00d4ff", str(num)
        bg = "rgba(0,212,255,0.1)"
        border = "#00d4ff"
    else:
        col, lbl = "#64748b", str(num)
        bg = "transparent"
        border = "#1e2a3a"
    return f"""
    <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;
                background:{bg};border:1px solid {border};border-radius:6px;
                margin-bottom:6px;cursor:pointer">
        <span style="width:22px;height:22px;background:{col};color:#0a0c10;
                     border-radius:50%;display:flex;align-items:center;justify-content:center;
                     font-family:JetBrains Mono,monospace;font-size:11px;font-weight:700;
                     flex-shrink:0">{lbl}</span>
        <span style="font-family:Syne,sans-serif;font-size:13px;font-weight:600;color:{'#e2e8f0' if (active or done) else '#64748b'}">{label}</span>
    </div>
    """

# ─── Session state ─────────────────────────────────────────────────────────────

STEPS = [
    "Basics",
    "Components",
    "Schedule",
    "Lambda Config",
    "Lambda Code",
    "Database",
    "Generate",
]

def init_state():
    defaults = {
        "step": 0,
        # Basics
        "pipeline_name": "",
        "pipeline_desc": "",
        "aws_region": "us-east-1",
        # Components
        "use_eventbridge": True,
        "use_sns": True,
        "use_rds": True,
        # Schedule
        "schedule_mode": "rate",
        "rate_value": 1,
        "rate_unit": "hours",
        "cron_minute": "0",
        "cron_hour": "2",
        "cron_dom": "*",
        "cron_month": "*",
        "cron_dow": "?",
        # Lambda config
        "runtime": "python3.12",
        "memory_mb": 256,
        "timeout_sec": 120,
        "arch": "x86_64",
        "env_vars": [],  # list of {"key": ..., "value": ..., "secret": bool}
        # Lambda code
        "handler_code": DEFAULT_HANDLER,
        "helper_files": {},  # filename -> content str
        "requirements": "psycopg2-binary==2.9.9\nrequests==2.31.0\n",
        # Database
        "db_table": "",
        "db_schema": [],   # list of {"col", "type", "pk", "nullable", "default"}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

DEFAULT_HANDLER = '''\
"""
Pipeline handler — implement your logic in run_pipeline().
"""

import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info("Event: %s", json.dumps(event, default=str))
    try:
        result = run_pipeline(event)
        return {"statusCode": 200, "body": json.dumps(result, default=str)}
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        raise


def run_pipeline(event: dict) -> dict:
    # TODO: implement your pipeline logic here
    #
    # Useful env vars (set in pipeline config):
    #   os.environ["DB_HOST"]
    #   os.environ["RPC_URL"]
    #
    records = 0
    return {"status": "ok", "records": records}
'''

init_state()

# ─── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 24px">
        <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;
                    color:#00d4ff;letter-spacing:-0.02em">⚡ Pipeline Builder</div>
        <div style="font-family:JetBrains Mono,monospace;font-size:11px;
                    color:#64748b;margin-top:4px">scaffold → commit → deploy</div>
    </div>
    """, unsafe_allow_html=True)

    current_step = st.session_state.step
    steps_html = ""
    for i, label in enumerate(STEPS):
        # Skip schedule step if no eventbridge
        if label == "Schedule" and not st.session_state.use_eventbridge:
            continue
        # Skip DB step if no RDS
        if label == "Database" and not st.session_state.use_rds:
            continue
        steps_html += step_pill(i + 1, label, active=(i == current_step), done=(i < current_step))
    st.markdown(steps_html, unsafe_allow_html=True)

    if st.session_state.pipeline_name:
        st.markdown("---")
        st.markdown(f"""
        <div style="font-family:JetBrains Mono,monospace">
            <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">Current pipeline</div>
            <div style="font-size:13px;color:#00d4ff;font-weight:600">{st.session_state.pipeline_name}</div>
            <div style="font-size:11px;color:#64748b;margin-top:4px">{st.session_state.aws_region}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    # Jump navigation
    for i, label in enumerate(STEPS):
        if label == "Schedule" and not st.session_state.use_eventbridge:
            continue
        if label == "Database" and not st.session_state.use_rds:
            continue
        if st.button(label, key=f"nav_{i}", use_container_width=True):
            st.session_state.step = i
            st.rerun()

# ─── Nav helpers ───────────────────────────────────────────────────────────────

def next_step():
    # Skip schedule if no eventbridge
    nxt = st.session_state.step + 1
    if nxt < len(STEPS):
        if STEPS[nxt] == "Schedule" and not st.session_state.use_eventbridge:
            nxt += 1
        if STEPS[nxt] == "Database" and not st.session_state.use_rds:
            nxt += 1
    st.session_state.step = min(nxt, len(STEPS) - 1)

def prev_step():
    prv = st.session_state.step - 1
    if prv >= 0:
        if STEPS[prv] == "Database" and not st.session_state.use_rds:
            prv -= 1
        if STEPS[prv] == "Schedule" and not st.session_state.use_eventbridge:
            prv -= 1
    st.session_state.step = max(prv, 0)

def nav_row(show_prev=True, next_label="Continue →", next_disabled=False):
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if show_prev and st.button("← Back"):
            prev_step(); st.rerun()
    with cols[2]:
        if st.button(next_label, type="primary", disabled=next_disabled):
            next_step(); st.rerun()

# ─── STEP 0: Basics ───────────────────────────────────────────────────────────

def step_basics():
    section_header("Pipeline basics", "Name and describe your pipeline")

    col1, col2 = st.columns([2, 1])
    with col1:
        name = st.text_input(
            "Pipeline name",
            value=st.session_state.pipeline_name,
            placeholder="arbitrum-block-fetcher",
            help="Kebab-case, e.g. arbitrum-block-fetcher",
        )
        if name:
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            if slug != name:
                st.info(f"Will be normalised to: `{slug}`")
            st.session_state.pipeline_name = slug

        desc = st.text_area(
            "Description",
            value=st.session_state.pipeline_desc,
            placeholder="Fetches Arbitrum block numbers at 2am daily and writes to PostgreSQL",
            height=80,
        )
        st.session_state.pipeline_desc = desc

    with col2:
        region = st.selectbox(
            "AWS Region",
            ["us-east-1", "us-east-2", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1"],
            index=["us-east-1","us-east-2","us-west-2","eu-west-1","eu-central-1","ap-southeast-1"].index(
                st.session_state.aws_region
            ),
        )
        st.session_state.aws_region = region

        ecr_repo = st.text_input(
            "ECR repo name",
            value=st.session_state.get("ecr_repo", "") or (st.session_state.pipeline_name + "-lambda" if st.session_state.pipeline_name else ""),
            placeholder="my-pipeline-lambda",
        )
        st.session_state.ecr_repo = ecr_repo

    nav_row(show_prev=False, next_disabled=not st.session_state.pipeline_name)

# ─── STEP 1: Components ────────────────────────────────────────────────────────

COMPONENT_INFO = {
    "Lambda": {
        "icon": "λ",
        "desc": "The compute layer. Runs your Python script as a containerised function.",
        "required": True,
        "color": "#f59e0b",
    },
    "EventBridge Scheduler": {
        "icon": "⏰",
        "desc": "Triggers your Lambda on a schedule (cron or rate expression).",
        "required": False,
        "key": "use_eventbridge",
        "color": "#00d4ff",
    },
    "SNS Failure Alert": {
        "icon": "🔔",
        "desc": "Sends a notification when the Lambda errors. Hooks into CloudWatch.",
        "required": False,
        "key": "use_sns",
        "color": "#a78bfa",
    },
    "PostgreSQL Target": {
        "icon": "🗄",
        "desc": "Generates a migration SQL file + GitHub Actions job to create the target table.",
        "required": False,
        "key": "use_rds",
        "color": "#10b981",
    },
}

def step_components():
    section_header("Select components", "Choose what AWS resources to provision")

    for comp_name, info in COMPONENT_INFO.items():
        enabled = info.get("required", False) or st.session_state.get(info.get("key", ""), False)
        col_card, col_check = st.columns([10, 1])
        with col_card:
            st.markdown(f"""
            <div style="background:#10141c;border:1px solid {''+info['color']+'' if enabled else '#1e2a3a'};
                        border-radius:8px;padding:14px 18px;display:flex;align-items:flex-start;
                        gap:14px;margin-bottom:8px;transition:border-color 0.15s">
                <div style="width:36px;height:36px;background:{'rgba('+','.join(str(int(info['color'].lstrip('#')[i:i+2],16)) for i in (0,2,4))+',0.15)'};
                             border-radius:6px;display:flex;align-items:center;justify-content:center;
                             font-size:16px;flex-shrink:0">{info['icon']}</div>
                <div>
                    <div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;
                                color:{'#e2e8f0' if enabled else '#64748b'};margin-bottom:3px">
                        {comp_name}
                        {'<span style="font-family:JetBrains Mono,monospace;font-size:10px;background:rgba(245,158,11,0.15);color:#f59e0b;padding:1px 7px;border-radius:3px;margin-left:8px">REQUIRED</span>' if info.get('required') else ''}
                    </div>
                    <div style="font-family:JetBrains Mono,monospace;font-size:12px;color:#64748b">{info['desc']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_check:
            if not info.get("required"):
                key = info["key"]
                val = st.checkbox("", value=st.session_state[key], key=f"comp_{key}", label_visibility="hidden")
                st.session_state[key] = val

    nav_row()

# ─── STEP 2: Schedule ──────────────────────────────────────────────────────────

def schedule_expression():
    mode = st.session_state.schedule_mode
    if mode == "rate":
        v = st.session_state.rate_value
        u = st.session_state.rate_unit
        unit = u.rstrip("s") if v == 1 else u
        return f"rate({v} {unit})"
    else:
        m  = st.session_state.cron_minute
        h  = st.session_state.cron_hour
        d  = st.session_state.cron_dom
        mo = st.session_state.cron_month
        dw = st.session_state.cron_dow
        return f"cron({m} {h} {d} {mo} {dw} *)"

def human_schedule():
    mode = st.session_state.schedule_mode
    if mode == "rate":
        v = st.session_state.rate_value
        u = st.session_state.rate_unit
        return f"Every {v} {u}"
    else:
        h = st.session_state.cron_hour.zfill(2)
        m = st.session_state.cron_minute.zfill(2)
        d = st.session_state.cron_dom
        dw = st.session_state.cron_dow
        if d == "*" and dw == "?":
            return f"Daily at {h}:{m} UTC"
        elif d != "*":
            return f"Day {d} of each month at {h}:{m} UTC"
        else:
            days = {"MON":"Monday","TUE":"Tuesday","WED":"Wednesday","THU":"Thursday",
                    "FRI":"Friday","SAT":"Saturday","SUN":"Sunday"}
            return f"Every {days.get(dw, dw)} at {h}:{m} UTC"

def step_schedule():
    section_header("Schedule", "When should your Lambda run?")

    mode = st.radio(
        "Schedule mode",
        ["rate", "cron"],
        format_func=lambda x: "⚡ Rate (every N minutes/hours/days)" if x == "rate" else "🕐 Cron (specific time)",
        horizontal=True,
        index=0 if st.session_state.schedule_mode == "rate" else 1,
    )
    st.session_state.schedule_mode = mode
    st.markdown("<br>", unsafe_allow_html=True)

    if mode == "rate":
        col1, col2 = st.columns(2)
        with col1:
            v = st.number_input("Every", min_value=1, max_value=9999,
                                value=st.session_state.rate_value, key="rate_v_input")
            st.session_state.rate_value = v
        with col2:
            u = st.selectbox("Unit", ["minutes", "hours", "days"],
                             index=["minutes","hours","days"].index(st.session_state.rate_unit))
            st.session_state.rate_unit = u
    else:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px">AWS Cron expression (UTC)</div>', unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        labels = ["Minute", "Hour", "Day of month", "Month", "Day of week"]
        keys   = ["cron_minute","cron_hour","cron_dom","cron_month","cron_dow"]
        placeholders = ["0","2","*","*","?"]
        for col, lbl, key, ph in zip([col1,col2,col3,col4,col5], labels, keys, placeholders):
            with col:
                val = st.text_input(lbl, value=st.session_state[key], placeholder=ph, key=f"ci_{key}")
                st.session_state[key] = val

        st.caption("Use `*` for every, `?` for either day-of-month OR day-of-week (not both). "
                   "Day-of-week: MON-SUN. AWS EventBridge adds an implicit `year` field.")

    expr = schedule_expression()
    human = human_schedule()
    st.markdown(f"""
    <div style="margin-top:20px;background:#0a0c10;border:1px solid #00d4ff;
                border-radius:8px;padding:16px 20px;display:flex;align-items:center;gap:20px">
        <div>
            <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#64748b;
                        text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">Expression</div>
            <div style="font-family:JetBrains Mono,monospace;font-size:16px;color:#00d4ff;
                        font-weight:600">{expr}</div>
        </div>
        <div style="width:1px;background:#1e2a3a;height:36px"></div>
        <div>
            <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#64748b;
                        text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">Runs</div>
            <div style="font-family:Syne,sans-serif;font-size:15px;color:#e2e8f0;
                        font-weight:600">{human}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_row()

# ─── STEP 3: Lambda config ─────────────────────────────────────────────────────

def step_lambda_config():
    section_header("Lambda configuration", "Memory, timeout, runtime, and environment variables")

    col1, col2 = st.columns(2)
    with col1:
        runtime = st.selectbox(
            "Runtime",
            ["python3.12", "python3.11", "python3.10"],
            index=["python3.12","python3.11","python3.10"].index(st.session_state.runtime),
        )
        st.session_state.runtime = runtime

        arch = st.selectbox(
            "Architecture",
            ["x86_64", "arm64"],
            index=["x86_64","arm64"].index(st.session_state.arch),
            help="arm64 (Graviton) is cheaper. Use x86_64 if unsure.",
        )
        st.session_state.arch = arch

    with col2:
        mem = st.select_slider(
            "Memory (MB)",
            options=[128, 256, 512, 1024, 2048, 4096],
            value=st.session_state.memory_mb,
        )
        st.session_state.memory_mb = mem

        timeout = st.slider(
            "Timeout (seconds)",
            min_value=10, max_value=900,
            value=st.session_state.timeout_sec,
            step=10,
        )
        st.session_state.timeout_sec = timeout

    st.markdown("---")
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:12px">Environment variables</div>', unsafe_allow_html=True)
    st.caption("Prefix the value with `ssm:` for secrets stored in AWS SSM Parameter Store — e.g. `ssm:/myapp/db-password`")

    # Add/remove env vars
    env_vars = st.session_state.env_vars

    to_delete = None
    for i, ev in enumerate(env_vars):
        col_k, col_v, col_s, col_d = st.columns([2, 3, 1, 0.5])
        with col_k:
            ev["key"] = st.text_input("Key", value=ev["key"], key=f"ev_k_{i}", label_visibility="collapsed", placeholder="KEY_NAME")
        with col_v:
            ev["value"] = st.text_input("Value", value=ev["value"], key=f"ev_v_{i}", label_visibility="collapsed", placeholder="value or ssm:/path/to/secret")
        with col_s:
            is_ssm = ev["value"].startswith("ssm:") if ev["value"] else False
            if is_ssm:
                st.markdown(f'<div style="padding-top:8px">{badge("SSM","#a78bfa")}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="padding-top:8px">{badge("PLAIN","#64748b")}</div>', unsafe_allow_html=True)
        with col_d:
            if st.button("✕", key=f"del_ev_{i}"):
                to_delete = i

    if to_delete is not None:
        env_vars.pop(to_delete)
        st.rerun()

    if st.button("+ Add variable"):
        env_vars.append({"key": "", "value": ""})
        st.rerun()

    nav_row()

# ─── STEP 4: Lambda code ───────────────────────────────────────────────────────

def step_lambda_code():
    section_header("Lambda code", "Paste your handler and upload any helper scripts")

    tab1, tab2, tab3 = st.tabs(["  handler.py  ", "  requirements.txt  ", "  helper scripts  "])

    with tab1:
        code = st.text_area(
            "Handler code",
            value=st.session_state.handler_code,
            height=400,
            help="Must contain a function named `handler(event, context)`",
            label_visibility="collapsed",
        )
        st.session_state.handler_code = code
        if "def handler" not in code:
            st.warning("⚠ handler.py must define a `handler(event, context)` function — this is the Lambda entry point.")

    with tab2:
        reqs = st.text_area(
            "requirements",
            value=st.session_state.requirements,
            height=200,
            label_visibility="collapsed",
            placeholder="psycopg2-binary==2.9.9\nrequests==2.31.0\n",
        )
        st.session_state.requirements = reqs

    with tab3:
        st.caption("Upload any Python helper modules that handler.py imports (e.g. `utils.py`, `db.py`).")
        uploaded = st.file_uploader(
            "Upload helper scripts",
            type=["py", "json", "yaml", "yml", "sql", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        for f in uploaded:
            content = f.read().decode("utf-8", errors="replace")
            st.session_state.helper_files[f.name] = content

        if st.session_state.helper_files:
            st.markdown(f'<div style="margin-top:8px">{badge(str(len(st.session_state.helper_files)) + " file(s) loaded","#10b981")}</div>', unsafe_allow_html=True)
            for fname in st.session_state.helper_files:
                col_f, col_x = st.columns([8, 1])
                with col_f:
                    st.markdown(f'<code style="font-size:12px">{fname}</code>', unsafe_allow_html=True)
                with col_x:
                    if st.button("✕", key=f"del_helper_{fname}"):
                        del st.session_state.helper_files[fname]
                        st.rerun()

    nav_row()

# ─── STEP 5: Database ──────────────────────────────────────────────────────────

PG_TYPES = ["TEXT","VARCHAR(255)","INTEGER","BIGINT","NUMERIC","BOOLEAN",
            "TIMESTAMP","TIMESTAMPTZ","DATE","JSONB","UUID","SERIAL","BIGSERIAL"]

def step_database():
    section_header("Target table schema", "Define the PostgreSQL table the pipeline will write to")

    col1, col2 = st.columns([2, 3])
    with col1:
        tbl = st.text_input(
            "Table name",
            value=st.session_state.db_table,
            placeholder="block_timestamps",
        )
        st.session_state.db_table = tbl.lower().replace(" ", "_") if tbl else tbl

    schema = st.session_state.db_schema

    st.markdown('<div style="font-family:Syne,sans-serif;font-size:15px;font-weight:700;color:#e2e8f0;margin:16px 0 8px">Columns</div>', unsafe_allow_html=True)

    # Column header
    hcols = st.columns([3, 2, 0.8, 0.8, 2, 0.5])
    for h, w in zip(["Column name","Type","PK","Nullable","Default",""], hcols):
        if h:
            w.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;padding-bottom:4px">{h}</div>', unsafe_allow_html=True)

    to_del = None
    for i, col in enumerate(schema):
        c1,c2,c3,c4,c5,c6 = st.columns([3, 2, 0.8, 0.8, 2, 0.5])
        with c1:
            col["col"] = st.text_input("col", value=col["col"], key=f"sc_col_{i}", label_visibility="collapsed", placeholder="column_name")
        with c2:
            col["type"] = st.selectbox("type", PG_TYPES, index=PG_TYPES.index(col.get("type","TEXT")), key=f"sc_type_{i}", label_visibility="collapsed")
        with c3:
            col["pk"] = st.checkbox("", value=col.get("pk", False), key=f"sc_pk_{i}")
        with c4:
            col["nullable"] = st.checkbox("", value=col.get("nullable", True), key=f"sc_null_{i}")
        with c5:
            col["default"] = st.text_input("def", value=col.get("default",""), key=f"sc_def_{i}", label_visibility="collapsed", placeholder="NULL")
        with c6:
            if st.button("✕", key=f"del_col_{i}"):
                to_del = i

    if to_del is not None:
        schema.pop(to_del)
        st.rerun()

    if st.button("+ Add column"):
        schema.append({"col":"","type":"TEXT","pk":False,"nullable":True,"default":""})
        st.rerun()

    if tbl and schema:
        st.markdown("---")
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px">SQL preview</div>', unsafe_allow_html=True)
        sql = generate_migration_sql(tbl, schema, preview=True)
        st.code(sql, language="sql")

    nav_row(next_label="Generate repo →")

# ─── FILE GENERATORS ──────────────────────────────────────────────────────────

def generate_migration_sql(table: str, schema: list, preview=False) -> str:
    if not table or not schema:
        return "-- No table defined"
    cols = []
    pk_cols = [c["col"] for c in schema if c.get("pk")]
    for c in schema:
        if not c["col"]:
            continue
        parts = [f'    "{c["col"]}" {c["type"]}']
        if not c.get("nullable", True):
            parts.append("NOT NULL")
        if c.get("default",""):
            parts.append(f"DEFAULT {c['default']}")
        cols.append(" ".join(parts))
    if pk_cols:
        cols.append(f'    PRIMARY KEY ({", ".join(pk_cols)})')
    col_sql = ",\n".join(cols)
    return f"""-- Migration: create {table}
-- Generated by Pipeline Builder on {datetime.utcnow().strftime('%Y-%m-%d')}

CREATE TABLE IF NOT EXISTS {table} (
{col_sql}
);
"""

def generate_dockerfile(runtime: str, arch: str) -> str:
    py = runtime.replace("python", "")
    platform = "linux/arm64" if arch == "arm64" else "linux/amd64"
    return f"""FROM --platform={platform} public.ecr.aws/lambda/python:{py}

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Copy all source files
COPY . ${{LAMBDA_TASK_ROOT}}

CMD ["handler.handler"]
"""

def generate_build_sh(name: str, region: str, ecr_repo: str, arch: str) -> str:
    platform = "linux/arm64" if arch == "arm64" else "linux/amd64"
    return f"""#!/usr/bin/env bash
# build.sh — Build the Lambda container image and push to ECR
# Usage: ./build.sh [image-tag]
set -euo pipefail

PIPELINE_NAME="{name}"
ECR_REPO="{ecr_repo}"
AWS_REGION="{region}"
AWS_ACCOUNT_ID="${{AWS_ACCOUNT_ID:?AWS_ACCOUNT_ID env var not set}}"
IMAGE_TAG="${{1:-$(git rev-parse --short HEAD)}}"

ECR_URI="${{AWS_ACCOUNT_ID}}.dkr.ecr.${{AWS_REGION}}.amazonaws.com/${{ECR_REPO}}"

echo "Building ${{ECR_URI}}:${{IMAGE_TAG}} ..."

# Authenticate with ECR
aws ecr get-login-password --region "${{AWS_REGION}}" \\
  | docker login --username AWS --password-stdin \\
    "${{AWS_ACCOUNT_ID}}.dkr.ecr.${{AWS_REGION}}.amazonaws.com"

# Create ECR repo if it doesn't exist
aws ecr describe-repositories --repository-names "${{ECR_REPO}}" \\
    --region "${{AWS_REGION}}" > /dev/null 2>&1 \\
  || aws ecr create-repository \\
       --repository-name "${{ECR_REPO}}" \\
       --region "${{AWS_REGION}}" \\
       --image-scanning-configuration scanOnPush=true

# Build & push
docker buildx build \\
  --platform {platform} \\
  --tag "${{ECR_URI}}:${{IMAGE_TAG}}" \\
  --tag "${{ECR_URI}}:latest" \\
  --push \\
  .

echo "✓ Pushed ${{ECR_URI}}:${{IMAGE_TAG}}"
"""

def generate_cfn_template(name: str, region: str, ecr_repo: str, arch: str,
                           memory: int, timeout: int, env_vars: list,
                           schedule_expr: str, use_eventbridge: bool,
                           use_sns: bool) -> str:
    # Build environment variables block — ssm: prefix uses dynamic references
    env_lines = ""
    for ev in env_vars:
        k, v = ev.get("key", ""), ev.get("value", "")
        if not k:
            continue
        if v and v.startswith("ssm:"):
            path = v[4:]
            env_lines += f"        {k}: '{{{{resolve:ssm:{path}}}}}'\n"
        else:
            env_lines += f"        {k}: '{v}'\n"
    env_block = f"      Variables:\n{env_lines}" if env_lines else ""

    sns_resources = ""
    sns_outputs = ""
    if use_sns:
        sns_resources = f"""
  FailureAlertTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: {name}-failures
      DisplayName: "{name} pipeline failures"

  LambdaErrorAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: {name}-errors
      AlarmDescription: Lambda errors in {name}
      Namespace: AWS/Lambda
      MetricName: Errors
      Dimensions:
        - Name: FunctionName
          Value: !Ref PipelineFunction
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 1
      ComparisonOperator: GreaterThanOrEqualToThreshold
      TreatMissingData: notBreaching
      AlarmActions:
        - !Ref FailureAlertTopic
"""
        sns_outputs = f"""
  FailureTopicArn:
    Description: Subscribe to this SNS topic to receive failure alerts
    Value: !Ref FailureAlertTopic
"""

    eventbridge_resources = ""
    if use_eventbridge:
        eventbridge_resources = f"""
  SchedulerRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: {name}-scheduler-role
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: scheduler.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: InvokeLambda
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action: lambda:InvokeFunction
                Resource: !GetAtt PipelineFunction.Arn

  PipelineSchedule:
    Type: AWS::Scheduler::Schedule
    Properties:
      Name: {name}-schedule
      ScheduleExpression: "{schedule_expr}"
      ScheduleExpressionTimezone: UTC
      FlexibleTimeWindow:
        Mode: "OFF"
      Target:
        Arn: !GetAtt PipelineFunction.Arn
        RoleArn: !GetAtt SchedulerRole.Arn
"""

    return f"""# CloudFormation template: {name}
# Generated by Pipeline Builder
# Deploy: aws cloudformation deploy --template-file infra/template.yaml \\
#           --stack-name {name} --capabilities CAPABILITY_NAMED_IAM \\
#           --parameter-overrides ImageTag=<tag>

AWSTemplateFormatVersion: "2010-09-09"
Description: "{name} — generated by Pipeline Builder"

Parameters:
  ImageTag:
    Type: String
    Default: latest
    Description: ECR image tag to deploy

Resources:

  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: {name}-lambda-role
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

  PipelineFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: {name}
      Description: !Sub "{name} — image ${{ImageTag}}"
      PackageType: Image
      Code:
        ImageUri: !Sub "${{AWS::AccountId}}.dkr.ecr.{region}.amazonaws.com/{ecr_repo}:${{ImageTag}}"
      Architectures:
        - {arch}
      Role: !GetAtt LambdaExecutionRole.Arn
      MemorySize: {memory}
      Timeout: {timeout}
      Environment:
{env_block if env_block else "        Variables: {}"}
{eventbridge_resources}{sns_resources}
Outputs:

  FunctionName:
    Description: Lambda function name
    Value: !Ref PipelineFunction

  FunctionArn:
    Description: Lambda function ARN
    Value: !GetAtt PipelineFunction.Arn
{sns_outputs}"""

def generate_workflow_ecr(name: str, region: str, ecr_repo: str) -> str:
    return f"""name: 1 — Build & push ECR image

on:
  workflow_dispatch:
    inputs:
      image_tag:
        description: 'Image tag (default: git SHA)'
        required: false
        default: ''
  push:
    branches: [main]
    paths:
      - 'lambda/**'
      - 'Dockerfile'
      - 'requirements.txt'

permissions:
  id-token: write
  contents: read

env:
  AWS_REGION: {region}
  ECR_REPO: {ecr_repo}

jobs:
  build-and-push:
    name: Build & push to ECR
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{{{ secrets.AWS_DEPLOY_ROLE_ARN }}}}
          aws-region: ${{{{ env.AWS_REGION }}}}

      - name: Set image tag
        id: tag
        run: |
          TAG="${{{{ inputs.image_tag }}}}"
          if [ -z "$TAG" ]; then TAG=$(git rev-parse --short HEAD); fi
          echo "tag=$TAG" >> "$GITHUB_OUTPUT"
          echo "Image tag: $TAG"

      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Create ECR repo (if not exists)
        run: |
          aws ecr describe-repositories --repository-names ${{{{ env.ECR_REPO }}}} \\
          || aws ecr create-repository --repository-name ${{{{ env.ECR_REPO }}}} \\
               --image-scanning-configuration scanOnPush=true

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{{{ steps.login-ecr.outputs.registry }}}}/${{{{ env.ECR_REPO }}}}:${{{{ steps.tag.outputs.tag }}}}
            ${{{{ steps.login-ecr.outputs.registry }}}}/${{{{ env.ECR_REPO }}}}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Output image URI
        run: |
          echo "✓ Pushed: ${{{{ steps.login-ecr.outputs.registry }}}}/${{{{ env.ECR_REPO }}}}:${{{{ steps.tag.outputs.tag }}}}"
          echo "image_uri=${{{{ steps.login-ecr.outputs.registry }}}}/${{{{ env.ECR_REPO }}}}:${{{{ steps.tag.outputs.tag }}}}" >> "$GITHUB_OUTPUT"
"""

def generate_workflow_lambda(name: str, region: str, ecr_repo: str) -> str:
    return f"""name: 2 — Deploy Lambda (CloudFormation)

on:
  workflow_dispatch:
    inputs:
      image_tag:
        description: 'ECR image tag to deploy'
        required: true
        default: 'latest'

permissions:
  id-token: write
  contents: read

env:
  AWS_REGION: {region}
  STACK_NAME: {name}

jobs:
  deploy:
    name: CloudFormation deploy
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{{{ secrets.AWS_DEPLOY_ROLE_ARN }}}}
          aws-region: ${{{{ env.AWS_REGION }}}}

      - name: Deploy stack
        run: |
          aws cloudformation deploy \\
            --template-file infra/template.yaml \\
            --stack-name ${{{{ env.STACK_NAME }}}} \\
            --capabilities CAPABILITY_NAMED_IAM \\
            --parameter-overrides ImageTag=${{{{ inputs.image_tag }}}} \\
            --region ${{{{ env.AWS_REGION }}}} \\
            --no-fail-on-empty-changeset

      - name: Print stack outputs
        run: |
          aws cloudformation describe-stacks \\
            --stack-name ${{{{ env.STACK_NAME }}}} \\
            --region ${{{{ env.AWS_REGION }}}} \\
            --query "Stacks[0].Outputs" \\
            --output table

      - name: Smoke test (invoke)
        run: |
          aws lambda invoke \\
            --function-name {name} \\
            --payload '{{}}' \\
            --region ${{{{ env.AWS_REGION }}}} \\
            /tmp/response.json
          cat /tmp/response.json
"""

def generate_workflow_migration(name: str, region: str, table: str) -> str:
    return f"""name: 3 — Apply DB migration

on:
  workflow_dispatch:
    inputs:
      confirm:
        description: 'Type the table name to confirm: {table}'
        required: true

permissions:
  id-token: write
  contents: read

env:
  AWS_REGION: {region}

jobs:
  apply-migration:
    name: Apply migration to PostgreSQL
    runs-on: ubuntu-latest
    if: inputs.confirm == '{table}'

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{{{ secrets.AWS_DEPLOY_ROLE_ARN }}}}
          aws-region: ${{{{ env.AWS_REGION }}}}

      - name: Fetch DB credentials from SSM
        id: db
        run: |
          DB_HOST=$(aws ssm get-parameter --name "/pipeline-factory/db-host" --query Parameter.Value --output text)
          DB_NAME=$(aws ssm get-parameter --name "/pipeline-factory/db-name" --query Parameter.Value --output text)
          DB_USER=$(aws ssm get-parameter --name "/pipeline-factory/db-user" --query Parameter.Value --output text)
          DB_PASS=$(aws ssm get-parameter --name "/pipeline-factory/db-password" --with-decryption --query Parameter.Value --output text)
          echo "::add-mask::$DB_PASS"
          echo "host=$DB_HOST" >> "$GITHUB_OUTPUT"
          echo "name=$DB_NAME" >> "$GITHUB_OUTPUT"
          echo "user=$DB_USER" >> "$GITHUB_OUTPUT"
          echo "pass=$DB_PASS" >> "$GITHUB_OUTPUT"

      - name: Apply migration
        env:
          PGHOST: ${{{{ steps.db.outputs.host }}}}
          PGDATABASE: ${{{{ steps.db.outputs.name }}}}
          PGUSER: ${{{{ steps.db.outputs.user }}}}
          PGPASSWORD: ${{{{ steps.db.outputs.pass }}}}
          PGSSLMODE: require
        run: |
          echo "Applying migration: migrations/V001__create_{table}.sql"
          psql -f migrations/V001__create_{table}.sql
          echo "✓ Migration applied"
"""

def generate_readme(name: str, desc: str, schedule_expr: str, region: str,
                    ecr_repo: str, use_rds: bool, table: str) -> str:
    migration_section = ""
    if use_rds and table:
        migration_section = f"""
## Database migration

Run **3 — Apply DB migration** workflow (type `{table}` to confirm).

This creates the `{table}` table in your PostgreSQL database.
"""
    return f"""# {name}

{desc}

> Generated by [Pipeline Builder](https://github.com/your-org/pipeline-builder) on {datetime.utcnow().strftime('%Y-%m-%d')}

---

## Deploy sequence

Run the GitHub Actions workflows in order:

| Step | Workflow | When |
|------|----------|------|
| 1 | **Build & push ECR image** | Every code change |
| 2 | **Deploy Lambda** | After step 1 |
| 3 | **Apply DB migration** | First deploy only |

---

## Local development

```bash
# Build image locally
./build.sh

# Invoke the handler directly (no AWS)
python -c "from lambda.handler import run_pipeline; print(run_pipeline({{}}))"

# Run in Docker (mimics Lambda environment)
docker build -t {name} .
docker run --rm \\
  -e AWS_REGION={region} \\
  -e DB_HOST=localhost \\
  {name} \\
  aws lambda invoke --function-name {name} --payload '{{}}' /tmp/out.json
```

## Schedule
`{schedule_expr}` (UTC)

## Resources

| Resource | Name |
|----------|------|
| Lambda | `{name}` |
| ECR repo | `{ecr_repo}` |
| Region | `{region}` |
{migration_section}
## Required GitHub secrets

| Secret | Description |
|--------|-------------|
| `AWS_ACCOUNT_ID` | Your 12-digit AWS account ID |
| `AWS_DEPLOY_ROLE_ARN` | IAM role for OIDC deploy (see docs) |
"""

# ─── STEP 6: Generate ──────────────────────────────────────────────────────────

def build_zip() -> bytes:
    s = st.session_state
    name = s.pipeline_name
    ecr_repo = s.get("ecr_repo") or f"{name}-lambda"
    schedule_expr = schedule_expression() if s.use_eventbridge else "manual"
    table = s.db_table
    schema = s.db_schema

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        root = f"{name}/"

        # Lambda source
        zf.writestr(root + "lambda/handler.py", s.handler_code)
        zf.writestr(root + "lambda/requirements.txt", s.requirements)
        for fname, content in s.helper_files.items():
            zf.writestr(root + f"lambda/{fname}", content)

        # Dockerfile + build.sh (at repo root — Docker context is whole repo)
        zf.writestr(root + "Dockerfile", generate_dockerfile(s.runtime, s.arch))
        zf.writestr(root + "requirements.txt", s.requirements)  # also at root for Docker
        build_sh = generate_build_sh(name, s.aws_region, ecr_repo, s.arch)
        zf.writestr(root + "build.sh", build_sh)

        # CloudFormation
        cfn = generate_cfn_template(
            name, s.aws_region, ecr_repo, s.arch,
            s.memory_mb, s.timeout_sec, s.env_vars,
            schedule_expr, s.use_eventbridge, s.use_sns,
        )
        zf.writestr(root + "infra/template.yaml", cfn)

        # GitHub Actions
        zf.writestr(root + ".github/workflows/1-deploy-ecr.yml", generate_workflow_ecr(name, s.aws_region, ecr_repo))
        zf.writestr(root + ".github/workflows/2-deploy-lambda.yml", generate_workflow_lambda(name, s.aws_region, ecr_repo))

        # Migration
        if s.use_rds and table and schema:
            sql = generate_migration_sql(table, schema)
            zf.writestr(root + f"migrations/V001__create_{table}.sql", sql)
            zf.writestr(root + ".github/workflows/3-apply-migration.yml",
                        generate_workflow_migration(name, s.aws_region, table))

        # Metadata
        config = {
            "name": name,
            "description": s.pipeline_desc,
            "aws_region": s.aws_region,
            "ecr_repo": ecr_repo,
            "runtime": s.runtime,
            "arch": s.arch,
            "memory_mb": s.memory_mb,
            "timeout_sec": s.timeout_sec,
            "schedule": schedule_expr,
            "components": {
                "eventbridge": s.use_eventbridge,
                "sns": s.use_sns,
                "rds": s.use_rds,
            },
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
        zf.writestr(root + "pipeline.json", json.dumps(config, indent=2))
        zf.writestr(root + "README.md", generate_readme(
            name, s.pipeline_desc, schedule_expr, s.aws_region,
            ecr_repo, s.use_rds, table,
        ))

    return buf.getvalue()

def step_generate():
    s = st.session_state
    name = s.pipeline_name
    ecr_repo = s.get("ecr_repo") or f"{name}-lambda"
    schedule_expr = schedule_expression() if s.use_eventbridge else "manual"
    table = s.db_table

    section_header("Generate repo", "Review and download your pipeline")

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pipeline", name)
    with col2:
        st.metric("Runtime", s.runtime)
    with col3:
        st.metric("Memory", f"{s.memory_mb} MB")
    with col4:
        st.metric("Schedule", schedule_expr if s.use_eventbridge else "Manual")

    st.markdown("---")

    # File tree
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:12px">Repo structure</div>', unsafe_allow_html=True)

    files = [
        (f"{name}/lambda/handler.py", "Your Lambda handler"),
        (f"{name}/lambda/requirements.txt", "Python dependencies"),
        (f"{name}/Dockerfile", "Lambda container image"),
        (f"{name}/build.sh", "Build & push to ECR"),
        (f"{name}/infra/template.yaml", "CloudFormation: Lambda + EventBridge + SNS"),
        (f"{name}/.github/workflows/1-deploy-ecr.yml", "CI: build & push image"),
        (f"{name}/.github/workflows/2-deploy-lambda.yml", "CI: update Lambda"),
        (f"{name}/pipeline.json", "Pipeline metadata"),
        (f"{name}/README.md", "Documentation"),
    ]
    if s.helper_files:
        for fn in s.helper_files:
            files.insert(2, (f"{name}/lambda/{fn}", "Helper script"))
    if s.use_rds and table:
        files.insert(-2, (f"{name}/migrations/V001__create_{table}.sql", "DB migration"))
        files.insert(-2, (f"{name}/.github/workflows/3-apply-migration.yml", "CI: apply migration"))

    tree_html = '<div style="background:#0a0c10;border:1px solid #1e2a3a;border-radius:8px;padding:16px;font-family:JetBrains Mono,monospace;font-size:12px">'
    for path, desc in files:
        parts = path.split("/")
        indent = "&nbsp;" * ((len(parts) - 1) * 4)
        fname = parts[-1]
        color = "#00d4ff" if fname.endswith(".py") else "#10b981" if fname.endswith(".yml") else "#a78bfa" if fname.endswith((".sql",".yaml")) else "#e2e8f0"
        tree_html += f'<div style="line-height:1.9">{indent}<span style="color:{color}">{fname}</span><span style="color:#475569;margin-left:12px;font-size:11px">{desc}</span></div>'
    tree_html += '</div>'
    st.markdown(tree_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # File previews
    with st.expander("Preview generated files"):
        tab_names = ["Dockerfile", "build.sh", "template.yaml", "1-deploy-ecr.yml"]
        tabs = st.tabs(tab_names)
        with tabs[0]:
            file_preview("Dockerfile", generate_dockerfile(s.runtime, s.arch))
        with tabs[1]:
            file_preview("build.sh", generate_build_sh(name, s.aws_region, ecr_repo, s.arch), "bash")
        with tabs[2]:
            file_preview("template.yaml", generate_cfn_template(name, s.aws_region, ecr_repo, s.arch,
                s.memory_mb, s.timeout_sec, s.env_vars, schedule_expr, s.use_eventbridge, s.use_sns), "yaml")
        with tabs[3]:
            file_preview("1-deploy-ecr.yml", generate_workflow_ecr(name, s.aws_region, ecr_repo), "yaml")

    st.markdown("<br>", unsafe_allow_html=True)

    # Big download button
    zip_bytes = build_zip()
    col_dl, col_info = st.columns([1, 2])
    with col_dl:
        st.download_button(
            label=f"⬇  Download {name}.zip",
            data=zip_bytes,
            file_name=f"{name}.zip",
            mime="application/zip",
        )
    with col_info:
        st.markdown(f"""
        <div style="font-family:JetBrains Mono,monospace;font-size:12px;color:#64748b;padding-top:8px">
            <div>Unzip → <code>git init && git push</code></div>
            <div style="margin-top:4px">Then run GitHub Actions workflows in order: 1 → 2 → 3</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col_back, _, col_new = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Back"):
            prev_step(); st.rerun()
    with col_new:
        if st.button("＋ New pipeline"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ─── Router ────────────────────────────────────────────────────────────────────

STEP_FNS = {
    0: step_basics,
    1: step_components,
    2: step_schedule,
    3: step_lambda_config,
    4: step_lambda_code,
    5: step_database,
    6: step_generate,
}

current = st.session_state.step
step_name = STEPS[current]

# Header
st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:28px;padding-bottom:20px;
            border-bottom:1px solid #1e2a3a">
    <div style="width:32px;height:32px;background:#00d4ff;color:#0a0c10;
                border-radius:6px;display:flex;align-items:center;justify-content:center;
                font-family:JetBrains Mono,monospace;font-size:13px;font-weight:700;
                flex-shrink:0">{current+1}</div>
    <div>
        <div style="font-family:Syne,sans-serif;font-size:24px;font-weight:800;
                    color:#e2e8f0;line-height:1">{step_name}</div>
        <div style="font-family:JetBrains Mono,monospace;font-size:11px;
                    color:#64748b;margin-top:3px">Step {current+1} of {len(STEPS)}</div>
    </div>
    <div style="flex:1"></div>
    <div style="display:flex;gap:4px">
        {''.join(['<div style="width:8px;height:8px;border-radius:50%;background:' + ('#00d4ff' if i==current else '#10b981' if i<current else '#1e2a3a') + '"></div>' for i in range(len(STEPS))])}
    </div>
</div>
""", unsafe_allow_html=True)

fn = STEP_FNS.get(current, step_basics)
fn()
