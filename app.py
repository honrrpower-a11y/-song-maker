
import streamlit as st
from gradio_client import Client
from pathlib import Path
import requests
import time

st.set_page_config(page_title="سازنده آهنگ", page_icon="🎵")

st.title("🎵 سازنده آهنگ")
st.write("خواسته‌ات را بنویس تا آهنگش را بسازیم.")

with st.form("song_form"):
    prompt = st.text_area(
        "چه آهنگی می‌خوای؟",
        placeholder="مثلاً: calm ambient music with soft piano"
    )
    submitted = st.form_submit_button("بساز")

if submitted:
    if not prompt.strip():
        st.warning("لطفاً توضیح آهنگ را بنویس.")
    else:
        try:
            # خواندن توکن اختیاری از Secrets
            try:
                token = st.secrets.get("HF_API_KEY", None)
            except Exception:
                token = None

            with st.spinner(
                "در حال اتصال به موتور ساخت موسیقی... "
                "ممکن است کمی طول بکشد."
            ):
                client_args = {"token": token} if token else {}
                client = Client(
                    "facebook/MusicGen",
                    **client_args
                )

            with st.spinner(
                "در صف ساخت آهنگ هستیم؛ لطفاً صبر کن... 🎶"
            ):
                result = client.predict(
                    prompt.strip(),
                    None,
                    fn_index=0
                )

            # در نسخه‌های مختلف Space ممکن است خروجی متفاوت باشد.
            audio_result = result

            if isinstance(result, (list, tuple)):
                if len(result) > 1 and result[1] is not None:
                    audio_result = result[1]
                elif len(result) > 0:
                    audio_result = result[0]

            # خروجی ممکن است مسیر فایل یا دیکشنری باشد.
            if isinstance(audio_result, dict):
                audio_result = (
                    audio_result.get("path")
                    or audio_result.get("url")
                    or audio_result.get("name")
                )

            if not audio_result:
                st.error("مدل اجرا شد، اما فایل صوتی برنگشت.")
                st.write("خروجی دریافتی:", result)

            elif isinstance(audio_result, str) and audio_result.startswith(
                ("http://", "https://")
            ):
                response = requests.get(
                    audio_result,
                    timeout=120
                )
                response.raise_for_status()
                audio_bytes = response.content

                st.success("آهنگ آماده است! 🎶")
                st.audio(audio_bytes)
                st.download_button(
                    "⬇️ دانلود آهنگ",
                    data=audio_bytes,
                    file_name="my_song.wav",
                    mime="audio/wav"
                )

            else:
                audio_path = Path(str(audio_result))

                if not audio_path.is_file():
                    st.error("فایل صوتی در مسیر برگشتی پیدا نشد.")
                    st.write("مسیر دریافتی:", str(audio_result))
                else:
                    audio_bytes = audio_path.read_bytes()

                    st.success("آهنگ آماده است! 🎶")
                    st.audio(audio_bytes)
                    st.download_button(
                        "⬇️ دانلود آهنگ",
                        data=audio_bytes,
                        file_name=audio_path.name,
                        mime="audio/wav"
                    )

        except Exception as e:
            error_text = str(e)
            st.error("ساخت آهنگ ناموفق بود.")
            st.write("جزئیات خطا:", error_text)

            if "429" in error_text or "rate limit" in error_text.lower():
                st.info(
                    "محدودیت درخواست ایجاد شده است. "
                    "کمی صبر کن و دوباره امتحان کن."
                )
            elif "401" in error_text or "403" in error_text:
                st.info(
                    "دسترسی رد شده است. توکن Hugging Face "
                    "و مجوزهای آن را بررسی کن."
                )
            else:
                st.info(
                    "ممکن است Space در دسترس نباشد یا "
                    "پارامترهای API آن تغییر کرده باشند."
                )
