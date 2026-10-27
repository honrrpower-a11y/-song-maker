
import streamlit as st
from gradio_client import Client
from pathlib import Path
import requests
import os

st.set_page_config(
    page_title="سازنده آهنگ",
    page_icon="🎵",
    layout="centered"
)

st.title("🎵 سازنده آهنگ")
st.write("توضیحت را بنویس تا تلاش کنیم آهنگش را بسازیم.")

with st.form("song_form"):
    prompt = st.text_area(
        "چه آهنگی می‌خوای؟",
        placeholder="مثلاً: calm ambient music with soft piano",
        height=120
    )
    submitted = st.form_submit_button(
        "🎶 بساز",
        use_container_width=True
    )

def get_hf_token():
    try:
        return st.secrets.get("HF_API_KEY", None)
    except Exception:
        return os.environ.get("HF_API_KEY")

def download_audio(result):
    """تبدیل خروجی Space به داده صوتی قابل پخش."""
    if isinstance(result, dict):
        result = (
            result.get("audio")
            or result.get("path")
            or result.get("url")
        )

    # بعضی APIها خروجی (sample_rate, audio_array) دارند.
    if (
        isinstance(result, tuple)
        and len(result) == 2
        and isinstance(result[0], (int, float))
    ):
        import numpy as np
        import io
        import wave

        sample_rate, audio_array = result
        audio_array = np.asarray(audio_array)

        if audio_array.dtype.kind == "f":
            audio_array = np.clip(
                audio_array, -1, 1
            )
            audio_array = (audio_array * 32767).astype(
                np.int16
            )

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(
                1 if audio_array.ndim == 1
                else audio_array.shape[1]
            )
            wav.setsampwidth(2)
            wav.setframerate(int(sample_rate))
            wav.writeframes(audio_array.tobytes())

        return buffer.getvalue(), "audio/wav", "my_song.wav"

    if isinstance(result, (list, tuple)):
        for item in reversed(result):
            try:
                return download_audio(item)
            except (ValueError, TypeError, OSError):
                continue
        raise ValueError("خروجی شامل فایل صوتی قابل استفاده نیست.")

    if isinstance(result, dict):
        raise ValueError("آدرس فایل صوتی در خروجی پیدا نشد.")

    if not isinstance(result, (str, os.PathLike)):
        raise ValueError(
            f"نوع خروجی صوتی پشتیبانی نمی‌شود: {type(result).__name__}"
        )

    value = str(result)

    if value.startswith(("https://", "http://")):
        response = requests.get(value, timeout=120)
        response.raise_for_status()
        content_type = response.headers.get(
            "Content-Type", ""
        )
        ext = ".mp3" if "mpeg" in content_type else ".wav"
        mime = "audio/mpeg" if ext == ".mp3" else "audio/wav"
        return response.content, mime, "my_song" + ext

    path = Path(value)
    if path.is_file():
        ext = path.suffix.lower()
        mime = {
            ".mp3": "audio/mpeg",
            ".ogg": "audio/ogg",
            ".wav": "audio/wav",
            ".flac": "audio/flac",
        }.get(ext, "audio/wav")
        return path.read_bytes(), mime, path.name

    raise ValueError("فایل صوتی در مسیر برگشتی پیدا نشد.")

if submitted:
    if not prompt.strip():
        st.warning("لطفاً توضیح آهنگ را بنویس.")
    else:
        try:
            token = get_hf_token()
            client_args = {"token": token} if token else {}

            with st.spinner(
                "در حال اتصال به سرویس موسیقی..."
            ):
                client = Client(
                    "facebook/MusicGen",
                    **client_args
                )

            with st.spinner(
                "در حال درخواست ساخت آهنگ؛ لطفاً صبر کن..."
            ):
                # نقطه پایانی متداول Space رسمی MusicGen
                result = client.predict(
                    prompt.strip(),
                    None,
                    api_name="/predict"
                )

            audio_bytes, mime, filename = download_audio(result)

            st.success("خروجی صوتی دریافت شد! 🎵")
            st.audio(audio_bytes, format=mime)

            st.download_button(
                "⬇️ دانلود آهنگ",
                data=audio_bytes,
                file_name=filename,
                mime=mime,
                use_container_width=True
            )

        except Exception as e:
            st.error("ساخت آهنگ ناموفق بود.")
            st.code(str(e))

            st.info(
                "اگر خطا درباره API یا تعداد ورودی‌هاست، "
                "باید مشخصات فعلی Space را بررسی کنیم. "
                "اگر خطا درباره دسترسی است، وضعیت Space "
                "و توکن را بررسی کن."
            )
