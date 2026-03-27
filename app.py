import streamlit as st
import spacy
from collections import defaultdict, Counter
import pandas as pd
import json
import re
import io

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Entity Extractor",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 {
    font-family: 'Space Mono', monospace !important;
}

.stApp {
    background: #0d0d0d;
    color: #f0f0f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111 !important;
    border-right: 1px solid #222;
}

/* Cards */
.entity-card {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s;
}
.entity-card:hover { border-color: #444; }

/* Entity tag colors */
.tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: 'Space Mono', monospace;
    margin-right: 4px;
    letter-spacing: 0.04em;
}

/* Macro badge */
.macro-badge {
    background: #1a1a2e;
    color: #7b8cde;
    border: 1px solid #2d3561;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    letter-spacing: 0.08em;
}
.micro-badge {
    background: #1a2e1f;
    color: #6dbf7b;
    border: 1px solid #2d6139;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    letter-spacing: 0.08em;
}

/* Metric boxes */
.metric-box {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 1.2rem;
    text-align: center;
}
.metric-box .num {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #c8a96e;
}
.metric-box .label {
    font-size: 0.8rem;
    color: #888;
    margin-top: 4px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* Highlighted text */
.highlighted-text {
    line-height: 2;
    font-size: 1rem;
    padding: 1.5rem;
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
}

/* Divider */
hr { border-color: #222 !important; }

/* Buttons */
.stButton > button {
    background: #c8a96e !important;
    color: #000 !important;
    border: none !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.5rem !important;
}
.stButton > button:hover {
    background: #e0c080 !important;
}

/* Text area */
.stTextArea textarea {
    background: #111 !important;
    color: #f0f0f0 !important;
    border: 1px solid #333 !important;
    font-family: 'DM Sans', sans-serif !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Entity config ─────────────────────────────────────────────────────────────

MACRO_ENTITIES = {
    "PERSON":   ("👤", "#7b8cde", "#1a1a2e"),
    "ORG":      ("🏢", "#de8c7b", "#2e1a1a"),
    "GPE":      ("🌍", "#7bde8c", "#1a2e1d"),
    "LOC":      ("📍", "#8cde7b", "#1d2e1a"),
    "EVENT":    ("🎯", "#deb87b", "#2e251a"),
    "WORK_OF_ART": ("🎨", "#de7bb8", "#2e1a25"),
    "LAW":      ("⚖️",  "#b87bde", "#221a2e"),
    "NORP":     ("🏳️", "#7bdecc", "#1a2e2b"),
    "FAC":      ("🏛️", "#ccde7b", "#292e1a"),
    "PRODUCT":  ("📦", "#de9f7b", "#2e201a"),
    "LANGUAGE": ("🗣️", "#7bb8de", "#1a222e"),
}

MICRO_ENTITIES = {
    "DATE":     ("📅", "#a8d8a8", "#1a2e1a"),
    "TIME":     ("⏰", "#d8d8a8", "#2e2e1a"),
    "MONEY":    ("💰", "#a8d8c8", "#1a2e28"),
    "PERCENT":  ("📊", "#c8a8d8", "#221a2e"),
    "QUANTITY": ("📏", "#d8c8a8", "#2e281a"),
    "ORDINAL":  ("🔢", "#a8c8d8", "#1a262e"),
    "CARDINAL": ("🔣", "#d8a8c8", "#2e1a26"),
}

# ── Load spaCy ────────────────────────────────────────────────────────────────
@st.cache_resource
def load_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        st.error("⚠️ spaCy model not found. Run: `python -m spacy download en_core_web_sm`")
        st.stop()

nlp = load_nlp()

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_entities(text: str):
    doc = nlp(text)
    macro, micro = [], []
    for ent in doc.ents:
        entry = {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
        if ent.label_ in MACRO_ENTITIES:
            macro.append(entry)
        elif ent.label_ in MICRO_ENTITIES:
            micro.append(entry)
    return macro, micro, doc


def build_highlighted_html(text: str, entities: list) -> str:
    all_ents = sorted(entities, key=lambda e: e["start"])
    html = ""
    prev = 0
    for ent in all_ents:
        html += text[prev:ent["start"]]
        label = ent["label"]
        if label in MACRO_ENTITIES:
            color, bg = MACRO_ENTITIES[label][1], MACRO_ENTITIES[label][2]
            cat = "MACRO"
        else:
            color, bg = MICRO_ENTITIES[label][1], MICRO_ENTITIES[label][2]
            cat = "MICRO"
        html += (
            f'<mark style="background:{bg};color:{color};border-radius:4px;'
            f'padding:1px 5px;font-weight:600;" title="{label} [{cat}]">'
            f'{ent["text"]}<sup style="font-size:0.6em;opacity:0.7;margin-left:2px">{label}</sup></mark>'
        )
        prev = ent["end"]
    html += text[prev:]
    return html


def entities_to_df(entities: list) -> pd.DataFrame:
    return pd.DataFrame(entities).drop(columns=["start", "end"], errors="ignore")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🔬 Entity Extractor")
    st.markdown("<small style='color:#666'>Micro & Macro NLP Analysis</small>", unsafe_allow_html=True)
    st.divider()

    input_mode = st.radio("Input Mode", ["✏️ Paste Text", "📄 Upload File"])

    st.divider()
    st.markdown("**Extraction Filters**")
    show_macro = st.checkbox("Macro Entities", value=True)
    show_micro = st.checkbox("Micro Entities", value=True)

    st.divider()
    st.markdown("**Macro** — high-level semantic")
    for label, (icon, color, _) in MACRO_ENTITIES.items():
        st.markdown(f"<span style='color:{color}'>{icon} {label}</span>", unsafe_allow_html=True)

    st.divider()
    st.markdown("**Micro** — granular numeric/temporal")
    for label, (icon, color, _) in MICRO_ENTITIES.items():
        st.markdown(f"<span style='color:{color}'>{icon} {label}</span>", unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────

st.markdown("# 🔬 ENTITY EXTRACTOR")
st.markdown("<p style='color:#666;font-size:0.9rem;margin-top:-8px'>Micro & Macro Named Entity Recognition · Powered by spaCy</p>", unsafe_allow_html=True)
st.divider()

text_input = ""

if input_mode == "✏️ Paste Text":
    text_input = st.text_area(
        "Paste your text below",
        height=200,
        placeholder="e.g. Apple Inc. was founded by Steve Jobs in Cupertino, California in 1976. The company earned $394.3 billion in revenue in 2022...",
    )
else:
    uploaded = st.file_uploader("Upload a .txt or .csv file", type=["txt", "csv"])
    if uploaded:
        if uploaded.name.endswith(".csv"):
            df_up = pd.read_csv(uploaded)
            col = st.selectbox("Select text column", df_up.columns.tolist())
            text_input = " ".join(df_up[col].dropna().astype(str).tolist())
        else:
            text_input = uploaded.read().decode("utf-8", errors="ignore")
        st.success(f"Loaded **{len(text_input):,}** characters")

run = st.button("⚡ EXTRACT ENTITIES")

# ── Results ───────────────────────────────────────────────────────────────────

if run and text_input.strip():
    with st.spinner("Analysing text..."):
        macro_ents, micro_ents, doc = extract_entities(text_input)

    all_ents = []
    if show_macro:
        all_ents += macro_ents
    if show_micro:
        all_ents += micro_ents

    # ── Metrics
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    metrics = [
        (len(text_input.split()), "WORDS"),
        (len(list(doc.sents)), "SENTENCES"),
        (len(macro_ents), "MACRO ENTITIES"),
        (len(micro_ents), "MICRO ENTITIES"),
    ]
    for c, (val, lbl) in zip(cols, metrics):
        with c:
            st.markdown(f'<div class="metric-box"><div class="num">{val}</div><div class="label">{lbl}</div></div>', unsafe_allow_html=True)

    st.divider()

    # ── Highlighted text
    st.markdown("### 📝 Annotated Text")
    highlighted = build_highlighted_html(text_input, all_ents)
    st.markdown(f'<div class="highlighted-text">{highlighted}</div>', unsafe_allow_html=True)
    st.divider()

    # ── Side-by-side breakdown
    left, right = st.columns(2)

    with left:
        st.markdown('<span class="macro-badge">MACRO ENTITIES</span>', unsafe_allow_html=True)
        st.markdown("")
        if macro_ents:
            freq = Counter(e["text"] for e in macro_ents)
            seen = set()
            for ent in macro_ents:
                if ent["text"] in seen:
                    continue
                seen.add(ent["text"])
                icon, color, bg = MACRO_ENTITIES.get(ent["label"], ("•", "#888", "#1a1a1a"))
                count = freq[ent["text"]]
                st.markdown(
                    f'<div class="entity-card">'
                    f'{icon} <strong style="color:{color}">{ent["text"]}</strong>'
                    f'&nbsp;&nbsp;<span class="tag" style="background:{bg};color:{color}">{ent["label"]}</span>'
                    f'{"&nbsp;<span style=\"color:#555;font-size:0.75rem\">×" + str(count) + "</span>" if count > 1 else ""}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown("<small style='color:#555'>No macro entities found.</small>", unsafe_allow_html=True)

    with right:
        st.markdown('<span class="micro-badge">MICRO ENTITIES</span>', unsafe_allow_html=True)
        st.markdown("")
        if micro_ents:
            freq = Counter(e["text"] for e in micro_ents)
            seen = set()
            for ent in micro_ents:
                if ent["text"] in seen:
                    continue
                seen.add(ent["text"])
                icon, color, bg = MICRO_ENTITIES.get(ent["label"], ("•", "#888", "#1a1a1a"))
                count = freq[ent["text"]]
                st.markdown(
                    f'<div class="entity-card">'
                    f'{icon} <strong style="color:{color}">{ent["text"]}</strong>'
                    f'&nbsp;&nbsp;<span class="tag" style="background:{bg};color:{color}">{ent["label"]}</span>'
                    f'{"&nbsp;<span style=\"color:#555;font-size:0.75rem\">×" + str(count) + "</span>" if count > 1 else ""}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown("<small style='color:#555'>No micro entities found.</small>", unsafe_allow_html=True)

    st.divider()

    # ── Export
    st.markdown("### 💾 Export Results")
    ec1, ec2, ec3 = st.columns(3)

    with ec1:
        if all_ents:
            df_export = entities_to_df(all_ents)
            csv_buf = df_export.to_csv(index=False)
            st.download_button("⬇ Download CSV", csv_buf, "entities.csv", "text/csv")

    with ec2:
        json_data = json.dumps({"macro": macro_ents, "micro": micro_ents}, indent=2)
        st.download_button("⬇ Download JSON", json_data, "entities.json", "application/json")

    with ec3:
        txt_lines = ["=== MACRO ENTITIES ===\n"]
        for e in macro_ents:
            txt_lines.append(f'{e["label"]}: {e["text"]}\n')
        txt_lines.append("\n=== MICRO ENTITIES ===\n")
        for e in micro_ents:
            txt_lines.append(f'{e["label"]}: {e["text"]}\n')
        st.download_button("⬇ Download TXT", "".join(txt_lines), "entities.txt", "text/plain")

elif run and not text_input.strip():
    st.warning("Please enter or upload some text first.")

# ── Footer
st.divider()
st.markdown(
    "<small style='color:#333'>Built with spaCy · Streamlit · en_core_web_sm</small>",
    unsafe_allow_html=True
)
