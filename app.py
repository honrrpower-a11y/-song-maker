
import streamlit as st
from gradio_client import Client
from pathlib import Path
import requests
import os
import io
import contextlib

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
        return st.secrets.get("HF_API_KEY")
    except Exception:
        return os.environ.get("HF_API_KEY")

def get_audio(result):
    if isinstance(result, dict):
        for key in ("audio", "path", "url", "video"):
            if result.get(key):
                return get_audio(result[key])

    if isinstance(result, (list, tuple)):
        for item in reversed(result):
            try:
                return get_audio(item)
            except (ValueError, TypeError, OSError):
                continue
        raise ValueError("فایل صوتی در خروجی پیدا نشد.")

    if isinstance(result, (str, os.PathLike)):
        value = str(result)

        if value.startswith(("https://", "http://")):
            response = requests.get(value, timeout=180)
            response.raise_for_status()
            return response.content, Path(value.split("?")[0]).suffix.lower()

        path = Path(value)
        if path.is_file():
            return path.read_bytes(), path.suffix.lower()

    raise ValueError(
        "سرویس فایل صوتی قابل دانلود برنگرداند. "
        f"نوع خروجی: {type(result).__name__}"
    )

if submitted:
    if not prompt.strip():
        st.warning("لطفاً توضیح آهنگ را بنویس.")
    else:
        try:
            token = get_hf_token()
            args = {"token": token} if token else {}

            with st.spinner("در حال اتصال به سرویس موسیقی..."):
                client = Client("facebook/MusicGen", **args)

            # دریافت مشخصات واقعی API
            with st.spinner("در حال بررسی تابع‌های سرویس..."):
                api_text = io.StringIO()
                with contextlib.redirect_stdout(api_text):
                    api_info = client.view_api(return_format="dict")

            if not isinstance(api_info, dict):
                raise RuntimeError(
                    "مشخصات API قابل خواندن نیست. "
                    "نسخه gradio_client را به‌روز کن."
                )

            named = api_info.get("named_endpoints", {})
            candidates = []

            for name, details in named.items():
                params = details.get("parameters", [])
                param_names = [
                    str(p.get("parameter_name", "")).lower()
                    for p in params
                ]
                if any(
                    word in pname
                    for pname in param_names
                    for word in ("text", "prompt", "description")
                ):
                    candidates.append((name, params, param_names))

            if not candidates:
                st.error("تابع مناسب ساخت آهنگ پیدا نشد.")
                st.write("تابع‌های موجود در سرویس:")
                st.code(api_text.getvalue() or str(api_info))
                st.stop()

            # انتخاب تابعی که ورودی متن آهنگ دارد
            endpoint, params, param_names = candidates[0]
            inputs = []

            for p, pname in zip(params, param_names):
                if any(x in pname for x in ("text", "prompt", "description")):
                    inputs.append(prompt.strip())
                elif "model" in pname or "version" in pname:
                    inputs.append("small")
                elif "melody" in pname or "audio" in pname:
                    inputs.append(None)
                elif "duration" in pname:
                    inputs.append(8)
                elif "topk" in pname or "top_k" in pname:
                    inputs.append(250)
                elif "topp" in pname or "top_p" in pname:
                    inputs.append(0.0)
                elif "temperature" in pname:
                    inputs.append(1.0)
                elif "cfg" in pname:
                    inputs.append(3.0)
                else:
                    # استفاده از مقدار پیش‌فرض اعلام‌شده در API
                    inputs.append(p.get("parameter_default", None))

            with st.spinner("در حال ساخت آهنگ؛ لطفاً صبر کن..."):
                result = client.predict(*inputs, api_name=endpoint)

            audio_bytes, ext = get_audio(result)

            mime_types = {
                ".wav": "audio/wav",
                ".mp3": "audio/mpeg",
                ".ogg": "audio/ogg",
                ".flac": "audio/flac",
                ".mp4": "video/mp4",
                ".webm": "video/webm",
            }
            mime = mime_types.get(ext, "application/octet-stream")

            if ext in (".mp4", ".webm"):
                st.success("خروجی سرویس دریافت شد.")
                st.video(audio_bytes)
            else:
                st.success("خروجی دریافت شد! 🎵")
                st.audio(audio_bytes, format=mime)

            st.download_button(
                "⬇️ دانلود خروجی",
                data=audio_bytes,
                file_name="my_song" + (ext or ".wav"),
                mime=mime,
                use_container_width=True
            )

        except Exception as e:
            st.error("ساخت آهنگ ناموفق بود.")
            st.code(f"{type(e).__name__}: {e}")
            st.info(
                "اگر خطای API دیدی، مشخصات Space یا ورودی‌های آن "
                "ممکن است تغییر کرده باشد. اگر خطای دسترسی دیدی، "
                "وضعیت Space و توکن Hugging Face را بررسی می‌کنیم."
            )
