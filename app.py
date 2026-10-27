import streamlit as st

st.set_page_config(page_title="سازنده آهنگ", page_icon="🎵")

st.title("🎵 سازنده آهنگ")
st.write("خواسته‌ات را بنویس تا آهنگش را بسازیم.")

with st.form("song_form"):
    prompt = st.text_area(
        "چه آهنگی می‌خوای؟",
        placeholder="مثلاً: آهنگ ترکی با باغلاما، صدای زن، ریتم ملایم"
    )
    submitted = st.form_submit_button("بساز")

if submitted:
    if prompt.strip():
        st.success("درخواست ثبت شد!")
        st.write("**خواسته شما:**", prompt)
        st.info("این نسخه آزمایشی است. اتصال به موتور آهنگ‌سازی به‌زودی اضافه می‌شود.")
    else:
        st.warning("لطفاً چیزی بنویس.")
