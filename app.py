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
UPLOAD_HELP = (
    "Supports WAV, MP3, FLAC, M4A, AAC, OGG, OPUS, AIFF, WMA, WebM, "
    "and other audio files ffmpeg can decode."
)
DECODE_ERROR_MESSAGE = (
    "This file could not be decoded. Try WAV, MP3, FLAC, AIFF, "
    "or another ffmpeg-supported audio file."
)
TUNE_ERROR_MESSAGE = (
    "This file could not be tuned or exported. Nothing was changed. "
    "Try WAV, MP3, FLAC, or AIFF, or use a smaller pitch shift."
)

AUDIO_MIME_TYPES = {
    ".aac": "audio/aac",
    ".ac3": "audio/ac3",
    ".aif": "audio/aiff",
    ".aiff": "audio/aiff",
    ".amr": "audio/amr",
    ".ape": "audio/ape",
    ".caf": "audio/x-caf",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".mp4": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".oga": "audio/ogg",
    ".ogg": "audio/ogg",
    ".opus": "audio/ogg",
    ".wav": "audio/wav",
    ".wave": "audio/wav",
    ".webm": "audio/webm",
    ".wma": "audio/x-ms-wma",
}

PCM_SUBTYPES = {"PCM_S8", "PCM_16", "PCM_24", "PCM_32", "FLOAT", "DOUBLE"}
EXPORT_FORMATS = {
    ".wav": {
        "suffix": ".wav",
        "format": "WAV",
        "default_subtype": "PCM_24",
        "label": "Download tuned WAV",
        "file_name": "tuned.wav",
        "mime": "audio/wav",
    },
    ".wave": {
        "suffix": ".wav",
        "format": "WAV",
        "default_subtype": "PCM_24",
        "label": "Download tuned WAV",
        "file_name": "tuned.wav",
        "mime": "audio/wav",
    },
    ".flac": {
        "suffix": ".flac",
        "format": "FLAC",
        "default_subtype": "PCM_24",
        "label": "Download tuned FLAC",
        "file_name": "tuned.flac",
        "mime": "audio/flac",
    },
    ".aif": {
        "suffix": ".aiff",
        "format": "AIFF",
        "default_subtype": "PCM_24",
        "label": "Download tuned AIFF",
        "file_name": "tuned.aiff",
        "mime": "audio/aiff",
    },
    ".aiff": {
        "suffix": ".aiff",
        "format": "AIFF",
        "default_subtype": "PCM_24",
        "label": "Download tuned AIFF",
        "file_name": "tuned.aiff",
        "mime": "audio/aiff",
    },
    ".mp3": {
        "suffix": ".mp3",
        "format": "MP3",
        "subtype": "MPEG_LAYER_III",
        "compression_level": 0.0,
        "label": "Download tuned MP3",
        "file_name": "tuned.mp3",
        "mime": "audio/mpeg",
    },
}
FALLBACK_EXPORT = EXPORT_FORMATS[".wav"]


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
            --studio-border: rgba(177, 108, 211, 0.18);
            --studio-text: #b16cd3;
            --studio-muted: #c7a3d8;
            --studio-accent: #b16cd3;
            --studio-accent-2: #c986e6;
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
            padding-top: 1.25rem;
            padding-bottom: 2.5rem;
            background: transparent;
        }}

        h1, h2, h3, p, label, span, div {{
            letter-spacing: 0;
        }}

        .hero {{
            background: transparent;
            border: 0;
            margin-bottom: 1rem;
            padding: 0.25rem 0 0.7rem;
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
            background: rgba(255, 255, 255, 0.035);
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
            background: rgba(255, 255, 255, 0.035);
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

        .custom-warning {{
            background: rgba(224, 168, 79, 0.12);
            border: 1px solid rgba(224, 168, 79, 0.38);
            border-radius: 8px;
            color: #f0c272;
            font-size: 0.86rem;
            line-height: 1.35;
            margin: -0.45rem 0 1rem;
            padding: 0.7rem 0.8rem;
        }}

        [data-testid="stFileUploader"] {{
            margin-bottom: 0.35rem;
        }}

        [data-testid="stFileUploaderDropzone"] {{
            background: #191919;
            border: 1px dashed rgba(177, 108, 211, 0.22);
            border-radius: 14px;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: var(--studio-border) !important;
            box-shadow: none !important;
        }}

        .stButton > button, .stDownloadButton > button {{
            border-radius: 8px;
            font-weight: 720;
            min-height: 2.85rem;
        }}

        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
            background: var(--studio-accent);
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

        .download-cue-row {{
            display: grid;
            gap: 2.25rem;
            grid-template-columns: 1.05fr 1fr 1.1fr;
            margin: -3.25rem 0 0.5rem;
        }}

        .download-cue-cell {{
            align-items: center;
            display: flex;
            justify-content: center;
        }}

        .download-jump {{
            align-items: center;
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            justify-content: center;
            opacity: 0.8;
            text-decoration: none !important;
            transition: opacity 160ms ease;
            width: max-content;
        }}

        .download-jump:hover,
        .download-jump:focus,
        .download-jump:visited {{
            opacity: 1;
            text-decoration: none !important;
        }}

        .download-jump-text {{
            color: #8f86a8;
            font-size: 0.62rem;
            font-weight: 750;
            letter-spacing: 0.3em;
            text-decoration: none !important;
            text-transform: uppercase;
        }}

        .download-jump-chevron {{
            animation: download-bounce 1.15s ease-in-out infinite;
            color: #8f86a8;
            font-size: 1.35rem;
            line-height: 1;
            text-decoration: none !important;
        }}

        @keyframes download-bounce {{
            0%, 100% {{
                transform: translateY(0);
            }}
            50% {{
                transform: translateY(0.35rem);
            }}
        }}

        @media (max-width: 760px) {{
            .download-cue-row {{
                display: flex;
                justify-content: center;
            }}
        }}

        .download-anchor {{
            scroll-margin-top: 0.75rem;
            height: 0;
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


def audio_mime_type(file_name):
    return AUDIO_MIME_TYPES.get(Path(file_name).suffix.lower())


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


def pitch_shift_audio(audio, sample_rate, semitone_shift):
    if abs(semitone_shift) < 0.001:
        return audio

    if audio.ndim == 1:
        return pyrb.pitch_shift(audio, sample_rate, semitone_shift)

    shifted_channels = [
        pyrb.pitch_shift(channel, sample_rate, semitone_shift) for channel in audio
    ]
    return np.vstack(shifted_channels)


def source_subtype(source_path):
    try:
        return sf.info(source_path).subtype
    except Exception:
        return None


def export_subtype(source_path, output_format, default_subtype):
    subtype = source_subtype(source_path)
    if subtype in PCM_SUBTYPES and subtype in sf.available_subtypes(output_format):
        return subtype
    return default_subtype


def export_config_for_source(source_path):
    return EXPORT_FORMATS.get(Path(source_path).suffix.lower(), FALLBACK_EXPORT)


def export_audio(audio, sample_rate, source_path):
    export_config = export_config_for_source(source_path)
    write_kwargs = {"format": export_config["format"]}

    if "subtype" in export_config:
        write_kwargs["subtype"] = export_config["subtype"]
    else:
        write_kwargs["subtype"] = export_subtype(
            source_path,
            export_config["format"],
            export_config["default_subtype"],
        )

    if "compression_level" in export_config:
        write_kwargs["compression_level"] = export_config["compression_level"]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=export_config["suffix"],
    ) as fixed_file:
        sf.write(
            fixed_file.name,
            audio.T if audio.ndim > 1 else audio,
            sample_rate,
            **write_kwargs,
        )
        return fixed_file.name


def shift_audio(file_path, semitone_shift):
    y, sr = librosa.load(file_path, sr=None, mono=False)
    y_shifted = pitch_shift_audio(y, sr, semitone_shift)
    return export_audio(y_shifted, sr, file_path)


def export_download_details(file_path):
    return export_config_for_source(file_path)


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
        </div>
        """,
        unsafe_allow_html=True,
    )


def reset_processed_output():
    st.session_state.pop("fixed_file_path", None)
    st.session_state.pop("last_shift", None)


def show_audio_error(message, exc):
    st.error(message)
    with st.expander("Technical details"):
        st.code(str(exc) or exc.__class__.__name__)


def render_tuned_audio(total_shift, spinner_text):
    with st.spinner(spinner_text):
        try:
            fixed_file_path = shift_audio(st.session_state.audio_path, total_shift)
            st.session_state.fixed_file_path = fixed_file_path
            st.session_state.last_shift = total_shift
        except Exception as exc:
            show_audio_error(TUNE_ERROR_MESSAGE, exc)


def show_custom_shift_warning(total_shift):
    if abs(total_shift) < 6:
        return

    st.markdown(
        """
        <div class="custom-warning">
            Extreme pitch shifts can make the result sound distorted or unstable.
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    uploaded_file = st.file_uploader("Upload audio file", help=UPLOAD_HELP)

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
    st.stop()

analysis = st.session_state.get("analysis")

left_col, middle_col, right_col = st.columns([1.05, 1, 1.1], gap="large")

with left_col:
    with st.container(border=True):
        st.markdown('<p class="section-title">Original Track</p>', unsafe_allow_html=True)
        st.write(st.session_state.uploaded_file_name)
        uploaded_mime_type = audio_mime_type(st.session_state.uploaded_file_name)
        if uploaded_mime_type:
            st.audio(st.session_state.uploaded_audio, format=uploaded_mime_type)

        if st.button("Analyze pitch", type="primary", use_container_width=True):
            with st.spinner("Listening for key and tuning offset..."):
                try:
                    analysis = analyze_audio(st.session_state.audio_path)
                    st.session_state.analysis = analysis
                    reset_processed_output()
                except Exception as exc:
                    show_audio_error(DECODE_ERROR_MESSAGE, exc)

if analysis:
    with middle_col:
        with st.container(border=True):
            st.markdown('<p class="section-title">Pitch Analysis</p>', unsafe_allow_html=True)
            render_analysis_metrics(analysis)

    with right_col:
        with st.container(border=True):
            st.markdown('<p class="section-title">Tuning Controls</p>', unsafe_allow_html=True)

            retune_shift = -(analysis["tuning_offset"] / 100)
            st.markdown(
                f"""
                <div class="shift-readout">
                    <span>Corrected key</span>
                    <strong>{analysis["detected_key"]}</strong>
                </div>
                <div class="shift-readout">
                    <span>Correction</span>
                    <strong>{signed_number(retune_shift)} st</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Apply retune", type="primary", use_container_width=True):
                render_tuned_audio(
                    retune_shift,
                    "Applying retune from the original upload...",
                )

            with st.expander("More pitch options"):
                mode = st.radio(
                    "Mode",
                    ["Change key", "Manual shift"],
                    horizontal=True,
                    on_change=reset_processed_output,
                )

                if mode == "Change key":
                    default_key = analysis["detected_key"]
                    desired_key = st.selectbox(
                        "Target key",
                        KEY_NAMES,
                        index=KEY_NAMES.index(default_key),
                        on_change=reset_processed_output,
                    )
                    key_shift = shortest_key_shift(analysis["detected_key"], desired_key)
                    total_shift = key_shift + retune_shift
                    shift_rows = f"""
                    <div class="shift-readout">
                        <span>Corrected key</span>
                        <strong>{desired_key}</strong>
                    </div>
                    <div class="shift-readout">
                        <span>Correction</span>
                        <strong>{signed_number(total_shift)} st</strong>
                    </div>
                    """
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
                    shift_rows = f"""
                    <div class="shift-readout">
                        <span>Correction</span>
                        <strong>{signed_number(total_shift)} st</strong>
                    </div>
                    """

                st.markdown(
                    shift_rows,
                    unsafe_allow_html=True,
                )
                show_custom_shift_warning(total_shift)

                if st.button("Apply retune", use_container_width=True):
                    render_tuned_audio(
                        total_shift,
                        "Applying retune from the original upload...",
                    )

if st.session_state.get("fixed_file_path"):
    st.markdown(
        """
        <div class="download-cue-row">
            <div></div>
            <div class="download-cue-cell">
                <a class="download-jump" href="#download-export">
                    <span class="download-jump-text">Scroll down</span>
                    <span class="download-jump-chevron">⌄</span>
                </a>
            </div>
            <div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div id="download-export" class="download-anchor"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            f'<p class="section-title">Tuned ({signed_number(st.session_state.last_shift)} st)</p>',
            unsafe_allow_html=True,
        )
        download_details = export_download_details(st.session_state.fixed_file_path)
        st.audio(st.session_state.fixed_file_path, format=download_details["mime"])

        with open(st.session_state.fixed_file_path, "rb") as fixed_file:
            st.download_button(
                label=download_details["label"],
                data=fixed_file,
                file_name=download_details["file_name"],
                mime=download_details["mime"],
                type="primary",
                use_container_width=True,
            )
