# Run this from inside your safenest-pk\safenest-pk folder:
#   .\update_to_groq.ps1
# Switches app.py to use Groq's free, OpenAI-compatible API instead of OpenAI.

@'
import os
import json
from pathlib import Path

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # reads GROQ_API_KEY from your .env file
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

PROMPT_DIR = Path("prompts")
SCHEMA_PATH = Path("schema/response_schema.json")


def load_text(path):
    return Path(path).read_text(encoding="utf-8")


system_prompt = load_text(PROMPT_DIR / "system_v1.txt")
safety_prompt = load_text(PROMPT_DIR / "safety_v1.txt")
tone_prompt = load_text(PROMPT_DIR / "tone_roman_urdu_v1.txt")
combined_system = f"{system_prompt}\n\n{safety_prompt}\n\n{tone_prompt}"

with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    response_schema = json.load(f)

st.set_page_config(page_title="SafeNest PK", page_icon="\U0001f6e1\ufe0f")
st.title("\U0001f6e1\ufe0f SafeNest PK")
st.caption("Privacy-first online safety support - koi bhi personal detail (naam, number, tasveer) na likhein.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            for step in msg["content"].get("checklist", []):
                st.markdown(f"- {step}")
            st.caption(msg["content"].get("disclaimer", ""))
        else:
            st.markdown(msg["content"])

user_input = st.chat_input("Apni problem batayein (Roman-Urdu, Urdu ya English mein)...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

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
            st.warning(reply.get("disclaimer", "Yeh sawal is chatbot ke scope se bahar hai."))
        else:
            st.markdown("**Checklist:**")
            for step in reply.get("checklist", []):
                st.markdown(f"- {step}")
            st.caption(reply.get("disclaimer", ""))
'@ | Set-Content -Path "app.py" -Encoding UTF8

@'
GROQ_API_KEY=your_key_here
'@ | Set-Content -Path ".env.example" -Encoding UTF8

Write-Host "Done! app.py now uses the free Groq API." -ForegroundColor Green
