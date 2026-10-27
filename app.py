import streamlit as st
import requests

st.set_page_config(page_title="سازنده آهنگ", page_icon="🎵")
st.title("🎵 سازنده آهنگ")
st.write("خواسته‌ات را بنویس تا آهنگش را بسازیم.")

# خواندن کلید از Secrets
HF_API_KEY = st.secrets["HF_API_KEY"]

with st.form("song_form"):
    prompt = st.text_area("چه آهنگی می‌خوای؟", placeholder="مثلاً: calm ambient music with soft piano")
    submitted = st.form_submit_button("بساز")

if submitted:
    if prompt.strip():
        with st.spinner("در حال ساخت آهنگ... (ممکنه ۱۰ تا ۳۰ ثانیه طول بکشه)"):
            # این آدرس جدیدتر و پایدارتر برای Hugging Face است
            API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
            headers = {"Authorization": f"Bearer {HF_API_KEY}"}
            payload = {"inputs": prompt}

            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

                if response.status_code == 200:
                    st.success("آهنگ ساخته شد! 🎶")
                    st.audio(response.content, format="audio/wav")
                elif response.status_code == 503:
                    st.warning("مدل در حال بیدار شدن است. لطفاً ۲۰ ثانیه صبر کن و دوباره بزن.")
                else:
                    st.error(f"خطا در ساخت آهنگ. کد خطا: {response.status_code}")
                    st.write(response.text) # این خط برای دیدن جزئیات خطا اضافه شده
            except Exception as e:
                st.error(f"مشکلی پیش آمد: {e}")
    else:
        st.warning("لطفاً چیزی بنویس.")
