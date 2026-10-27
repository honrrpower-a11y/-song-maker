import streamlit as st
import requests

st.set_page_config(page_title="سازنده آهنگ", page_icon="🎵")
st.title("🎵 سازنده آهنگ")

HF_API_KEY = st.secrets["HF_API_KEY"]

with st.form("song_form"):
    prompt = st.text_area("چه آهنگی می‌خوای؟")
    submitted = st.form_submit_button("بساز")

if submitted and prompt:
    with st.spinner("در حال ساخت..."):
        API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {"inputs": prompt, "parameters": {"duration": 8}}
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                st.success("آهنگ ساخته شد! 🎶")
                st.audio(response.content, format="audio/wav")
            else:
                st.error(f"خطا. کد: {response.status_code}")
        except Exception as e:
            st.error(f"مشکل: {e}")
