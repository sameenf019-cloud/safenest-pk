import os
import json
from pathlib import Path

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

PROMPT_DIR = Path("prompts")
SCHEMA_PATH = Path("schema/response_schema.json")


def load_text(path):
    return Path(path).read_text(encoding="utf-8-sig")


system_prompt = load_text(PROMPT_DIR / "system_v1.txt")
safety_prompt = load_text(PROMPT_DIR / "safety_v1.txt")
tone_prompt = load_text(PROMPT_DIR / "tone_roman_urdu_v1.txt")
combined_system = f"{system_prompt}\n\n{safety_prompt}\n\n{tone_prompt}"

with open(SCHEMA_PATH, "r", encoding="utf-8-sig") as f:
    response_schema = json.load(f)

st.set_page_config(page_title="SafeNest PK", page_icon="\U0001f6e1\ufe0f", layout="wide")

# ---------- 3D / glass-style CSS ----------
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top left, #1e2749 0%, #0d1117 55%, #090b10 100%);
}
[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 4px 8px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.35), 0 2px 4px rgba(0,0,0,0.25);
    backdrop-filter: blur(6px);
    background: rgba(30, 39, 73, 0.55);
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 10px;
    transition: transform 0.15s ease;
}
[data-testid="stChatMessage"]:hover {
    transform: translateY(-2px);
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.quick-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 10px 14px;
    margin-bottom: 8px;
    box-shadow: 0 6px 14px rgba(0,0,0,0.3);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.quick-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 22px rgba(0,0,0,0.45);
}
div.stButton > button {
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    transition: transform 0.12s ease;
}
div.stButton > button:hover {
    transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### \U0001f6e1\ufe0f SafeNest PK")
    st.caption("Roman-Urdu / Urdu / English support")

    st.markdown("**Yeh madad kar sakta hai:**")
    categories = [
        ("\U0001f4f5", "Online Harassment"),
        ("\U0001f4b8", "Scams"),
        ("\U0001f512", "Blackmail / Sextortion"),
        ("\U0001f464", "Fake Accounts"),
        ("\U0001f3ad", "Deepfakes"),
    ]
    for icon, label in categories:
        st.markdown(f"<div class='quick-card'>{icon} &nbsp; {label}</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("**Emergency / Official contacts**")
    st.markdown("- [FIA Cybercrime Wing](https://cybercrime.gov.pk)")
    st.markdown("- Digital Rights Foundation Helpline")

    st.divider()
    st.caption("\U0001f512 Koi chat ya personal data save nahi hota.")

    if st.button("\U0001f5d1\ufe0f Naya conversation shuru karein"):
        st.session_state.messages = []
        st.rerun()

# ---------- Header ----------
st.markdown("<div class='hero-title'>\U0001f6e1\ufe0f SafeNest PK</div>", unsafe_allow_html=True)
st.caption("Privacy-first online safety support - koi bhi personal detail (naam, number, tasveer) na likhein.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Quick-start examples (only before first message) ----------
if not st.session_state.messages:
    st.markdown("**Jaldi shuru karo:**")
    examples = [
        "Koi ajnabi mujhe harass kar raha hai",
        "Mujhe lottery scam message mila hai",
        "Koi mujhe blackmail kar raha hai",
    ]
    cols = st.columns(len(examples))
    for col, ex in zip(cols, examples):
        if col.button(ex):
            st.session_state.pending_input = ex

# ---------- Render history ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            if msg["content"].get("is_refusal"):
                st.warning(msg["content"].get("message") or msg["content"].get("disclaimer", ""))
            else:
                for step in msg["content"].get("checklist", []):
                    st.markdown(f"- {step}")
                st.caption(msg["content"].get("disclaimer", ""))
        else:
            st.markdown(msg["content"])

# ---------- Get input (typed or quick-start button) ----------
user_input = st.chat_input("Apni problem batayein (Roman-Urdu, Urdu ya English mein)...")
if not user_input and "pending_input" in st.session_state:
    user_input = st.session_state.pop("pending_input")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Sochte hain... \U0001f6e1\ufe0f"):
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": combined_system},
                {"role": "user", "content": user_input},
            ],
            response_format={"type": "json_schema", "json_schema": response_schema},
        )
        reply = json.loads(response.choices[0].message.content)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        if reply.get("is_refusal"):
            st.warning(reply.get("message") or reply.get("disclaimer", "Yeh sawal is chatbot ke scope se bahar hai."))
        else:
            st.markdown("**Checklist:**")
            for step in reply.get("checklist", []):
                st.markdown(f"- {step}")
            st.caption(reply.get("disclaimer", ""))
