from pathlib import Path
import tempfile

import librosa
import numpy as np
import pyrubberband as pyrb
import soundfile as sf
import streamlit as st


KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

LINKEDIN_PROFILE = "https://www.linkedin.com/in/skanda-vyas"
LINKEDIN_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png"
DONATION_LINK = "https://buymeacoffee.com/golgiwaffles"
DONATION_IMAGE = "https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"
FEEDBACK_LINK = "https://forms.gle/nWfGButqLA1w48zC8"


st.set_page_config(
    page_title="Skanda's Pitch Tuner",
    page_icon="music",
    layout="wide",
)


def inject_styles():
    st.markdown(
        f"""
        <style>
        :root {{
            --studio-bg: #121212;
            --studio-panel: #222222;
            --studio-panel-2: #222222;
            --studio-border: #343434;
            --studio-text: #b16cd3;
            --studio-muted: #c7a3d8;
            --studio-accent: #c45cff;
            --studio-accent-2: #ff5fc8;
            --studio-warn: #e0a84f;
        }}

        html {{
            accent-color: var(--studio-accent);
        }}

        .stApp {{
            background: var(--studio-bg);
            accent-color: var(--studio-accent);
        }}

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {{
            background: var(--studio-bg);
        }}

        .block-container {{
            max-width: 1180px;
            padding-top: 1.5rem;
            padding-bottom: 4rem;
            background: transparent;
        }}

        h1, h2, h3, p, label, span, div {{
            letter-spacing: 0;
        }}

        .hero {{
            background: var(--studio-panel);
            border: 1px solid var(--studio-border);
            border-radius: 12px;
            margin-bottom: 1rem;
            padding: 1rem 1.25rem 1.2rem;
        }}

        .hero h1 {{
            color: var(--studio-text);
            font-size: clamp(2rem, 4vw, 3.4rem);
            line-height: 0.95;
            margin: 0;
            text-wrap: balance;
        }}

        .metric-row {{
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            margin: 0.35rem 0 1rem;
        }}

        .metric {{
            align-items: center;
            background: var(--studio-panel);
            border: 1px solid var(--studio-border);
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            min-height: 3.2rem;
            padding: 0.7rem 0.85rem;
        }}

        .metric .label {{
            color: var(--studio-muted);
            display: block;
            font-size: 0.9rem;
            line-height: 1.25;
            margin: 0;
        }}

        .metric .value {{
            color: var(--studio-text);
            display: block;
            font-size: 1.15rem;
            font-weight: 750;
            line-height: 1.1;
            overflow-wrap: anywhere;
            text-align: right;
        }}

        .metric .value.accent {{
            color: var(--studio-accent);
        }}

        .section-title {{
            color: var(--studio-text);
            font-size: 1rem;
            font-weight: 720;
            margin: 0 0 0.45rem;
        }}

        .section-copy {{
            color: var(--studio-muted);
            font-size: 0.95rem;
            line-height: 1.5;
            margin: 0 0 1rem;
        }}

        .hint {{
            color: var(--studio-muted);
            font-size: 0.86rem;
            margin-top: 0.55rem;
        }}

        .shift-readout {{
            align-items: center;
            background: var(--studio-panel);
            border: 1px solid var(--studio-border);
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            margin: 0.5rem 0 1rem;
            padding: 0.85rem 1rem;
        }}

        .shift-readout span {{
            color: var(--studio-muted);
            font-size: 0.88rem;
        }}

        .shift-readout strong {{
            color: var(--studio-text);
            font-size: 1.35rem;
        }}

        [data-testid="stFileUploader"] {{
            margin-bottom: 0.35rem;
        }}

        [data-testid="stFileUploaderDropzone"] {{
            background: #191919;
            border: 1px dashed #464646;
            border-radius: 14px;
        }}

        .stButton > button, .stDownloadButton > button {{
            border-radius: 8px;
            font-weight: 720;
            min-height: 2.85rem;
        }}

        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
            background: linear-gradient(135deg, var(--studio-accent), var(--studio-accent-2));
            border-color: var(--studio-accent);
            color: #ffffff;
        }}

        .stButton > button[kind="primary"]:hover,
        .stDownloadButton > button[kind="primary"]:hover {{
            border-color: var(--studio-accent-2);
            color: #ffffff;
            filter: brightness(1.05);
        }}

        audio {{
            accent-color: var(--studio-accent);
        }}

        audio::-webkit-media-controls-play-button,
        audio::-webkit-media-controls-mute-button,
        audio::-webkit-media-controls-timeline,
        audio::-webkit-media-controls-volume-slider {{
            filter: hue-rotate(72deg) saturate(1.4);
        }}

        div[data-testid="stSpinner"] > div {{
            border-top-color: var(--studio-accent) !important;
            border-right-color: var(--studio-accent-2) !important;
        }}

        .stProgress > div > div > div > div {{
            background-color: var(--studio-accent);
        }}

        .download-jump {{
            align-items: center;
            background: linear-gradient(135deg, var(--studio-accent), var(--studio-accent-2));
            border-radius: 999px;
            bottom: 18px;
            color: #ffffff;
            display: flex;
            font-size: 1.35rem;
            font-weight: 800;
            height: 3rem;
            justify-content: center;
            left: 50%;
            position: fixed;
            text-decoration: none;
            transform: translateX(-50%);
            width: 3rem;
            z-index: 60;
        }}

        .download-anchor {{
            scroll-margin-top: 1.25rem;
        }}

        .floating-linkedin {{
            bottom: 18px;
            left: 18px;
            position: fixed;
            z-index: 50;
        }}

        .floating-linkedin img {{
            border-radius: 8px;
            width: 42px;
        }}

        .floating-donation {{
            bottom: 72px;
            position: fixed;
            right: 18px;
            z-index: 50;
        }}

        .floating-donation img {{
            width: 132px;
        }}

        .floating-feedback {{
            background-color: #f3f5f8;
            border-radius: 8px;
            bottom: 126px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.18);
            color: #141821;
            font-size: 13px;
            font-weight: 700;
            padding: 8px 12px;
            position: fixed;
            right: 18px;
            text-decoration: none;
            z-index: 50;
        }}

        @media (max-width: 760px) {{
            .metric-row {{
                grid-template-columns: 1fr;
            }}

            .floating-donation, .floating-feedback, .floating-linkedin {{
                display: none;
            }}
        }}
        </style>

        <a class="floating-linkedin" href="{LINKEDIN_PROFILE}" target="_blank">
            <img src="{LINKEDIN_IMAGE}" alt="LinkedIn Profile">
        </a>
        <a class="floating-donation" href="{DONATION_LINK}" target="_blank">
            <img src="{DONATION_IMAGE}" alt="Support this project">
        </a>
        <a class="floating-feedback" href="{FEEDBACK_LINK}" target="_blank">Feedback?</a>
        """,
        unsafe_allow_html=True,
    )


def save_uploaded_file(uploaded_file):
    suffix = Path(uploaded_file.name).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        return temp_file.name


def analyze_audio(file_path):
    y, sr = librosa.load(file_path, sr=None, mono=True)
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    key_scores = np.mean(chroma, axis=1)
    key_index = int(np.argmax(key_scores))
    detected_key = KEY_NAMES[key_index]
    tuning_offset = float(librosa.estimate_tuning(y=y, sr=sr) * 100)
    duration = float(librosa.get_duration(y=y, sr=sr))
    confidence = float(key_scores[key_index] / np.maximum(np.sum(key_scores), 1e-9))
    return {
        "detected_key": detected_key,
        "tuning_offset": tuning_offset,
        "duration": duration,
        "sample_rate": sr,
        "confidence": confidence,
    }


def shortest_key_shift(from_key, to_key):
    raw_shift = KEY_NAMES.index(to_key) - KEY_NAMES.index(from_key)
    return ((raw_shift + 6) % 12) - 6


def format_duration(seconds):
    minutes = int(seconds // 60)
    remainder = int(round(seconds % 60))
    return f"{minutes}:{remainder:02d}"


def signed_number(value, decimals=2):
    return f"{value:+.{decimals}f}"


def shift_audio(file_path, semitone_shift):
    y, sr = librosa.load(file_path, sr=None, mono=True)
    if abs(semitone_shift) < 0.001:
        y_shifted = y
    else:
        y_shifted = pyrb.pitch_shift(y, sr, semitone_shift)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fixed_file:
        sf.write(fixed_file.name, y_shifted, sr)
        return fixed_file.name


def show_metric(label, value, accent=False):
    accent_class = " accent" if accent else ""
    st.markdown(
        f"""
        <div class="metric">
            <span class="label">{label}</span>
            <span class="value{accent_class}">{value}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analysis_metrics(analysis):
    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric">
                <span class="label">Detected key</span>
                <span class="value accent">{analysis["detected_key"]}</span>
            </div>
            <div class="metric">
                <span class="label">Tuning offset</span>
                <span class="value">{signed_number(analysis["tuning_offset"])} cents</span>
            </div>
            <div class="metric">
                <span class="label">Duration</span>
                <span class="value">{format_duration(analysis["duration"])}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def reset_processed_output():
    st.session_state.pop("fixed_file_path", None)
    st.session_state.pop("last_shift", None)


inject_styles()

st.markdown(
    """
    <div class="hero">
        <h1>Skanda's Pitch Tuner</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    uploaded_file = st.file_uploader("Upload WAV or MP3", type=["wav", "mp3"])

if uploaded_file:
    file_signature = (uploaded_file.name, uploaded_file.size)
    if st.session_state.get("file_signature") != file_signature:
        st.session_state.file_signature = file_signature
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.uploaded_audio = uploaded_file.getvalue()
        st.session_state.audio_path = save_uploaded_file(uploaded_file)
        st.session_state.pop("analysis", None)
        reset_processed_output()

if not st.session_state.get("audio_path"):
    st.info("Upload a WAV or MP3 to begin.")
    st.stop()

left_col, middle_col, right_col = st.columns([1.05, 1, 1.1], gap="large")

with left_col:
    with st.container(border=True):
        st.markdown('<p class="section-title">Original Track</p>', unsafe_allow_html=True)
        st.write(st.session_state.uploaded_file_name)
        st.audio(st.session_state.uploaded_audio)

        if st.button("Analyze pitch", type="primary", use_container_width=True):
            with st.spinner("Listening for key and tuning offset..."):
                try:
                    st.session_state.analysis = analyze_audio(st.session_state.audio_path)
                    reset_processed_output()
                except Exception as exc:
                    st.error(f"Could not analyze this file: {exc}")

analysis = st.session_state.get("analysis")

with middle_col:
    with st.container(border=True):
        st.markdown('<p class="section-title">Pitch Analysis</p>', unsafe_allow_html=True)

        if analysis:
            render_analysis_metrics(analysis)

            st.caption(
                f'Sample rate: {analysis["sample_rate"]:,} Hz. Key confidence: {analysis["confidence"]:.0%}.'
            )
        else:
            st.empty()

with right_col:
    with st.container(border=True):
        st.markdown('<p class="section-title">Tuning Controls</p>', unsafe_allow_html=True)

        if not analysis:
            st.selectbox("Target key", KEY_NAMES, disabled=True)
            st.button("Render tuned audio", disabled=True, use_container_width=True)
        else:
            mode = st.radio(
                "Mode",
                ["Match key", "Manual shift"],
                horizontal=True,
                on_change=reset_processed_output,
            )

            if mode == "Match key":
                default_key = analysis["detected_key"]
                desired_key = st.selectbox(
                    "Target key",
                    KEY_NAMES,
                    index=KEY_NAMES.index(default_key),
                    on_change=reset_processed_output,
                )
                correct_tuning = st.checkbox(
                    "Correct tuning offset",
                    value=True,
                    on_change=reset_processed_output,
                )
                key_shift = shortest_key_shift(analysis["detected_key"], desired_key)
                fine_shift = -(analysis["tuning_offset"] / 100) if correct_tuning else 0
                total_shift = key_shift + fine_shift
                shift_label = f'{analysis["detected_key"]} to {desired_key}'
            else:
                manual_semitones = st.slider(
                    "Semitones",
                    min_value=-12,
                    max_value=12,
                    value=0,
                    step=1,
                    on_change=reset_processed_output,
                )
                manual_cents = st.slider(
                    "Cents",
                    min_value=-100,
                    max_value=100,
                    value=0,
                    step=1,
                    on_change=reset_processed_output,
                )
                total_shift = manual_semitones + (manual_cents / 100)
                shift_label = "Manual"

            st.markdown(
                f"""
                <div class="shift-readout">
                    <span>{shift_label}</span>
                    <strong>{signed_number(total_shift)} st</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Render tuned audio", type="primary", use_container_width=True):
                with st.spinner("Rendering from the original upload..."):
                    try:
                        fixed_file_path = shift_audio(st.session_state.audio_path, total_shift)
                        st.session_state.fixed_file_path = fixed_file_path
                        st.session_state.last_shift = total_shift
                    except Exception as exc:
                        st.error(f"Could not tune this file: {exc}")

if st.session_state.get("fixed_file_path"):
    st.markdown('<a class="download-jump" href="#download-export">↓</a>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<div id="download-export" class="download-anchor"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            f'<p class="section-title">Tuned ({signed_number(st.session_state.last_shift)} st)</p>',
            unsafe_allow_html=True,
        )
        st.audio(st.session_state.fixed_file_path, format="audio/wav")

        with open(st.session_state.fixed_file_path, "rb") as fixed_file:
            st.download_button(
                label="Download tuned WAV",
                data=fixed_file,
                file_name="tuned.wav",
                mime="audio/wav",
                type="primary",
                use_container_width=True,
            )
