import streamlit as st
import librosa
import numpy as np
import soundfile as sf
import tempfile
import os
import pyrubberband as pyrb
KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
linkedin_profile = "https://www.linkedin.com/in/skanda-vyas"
linkedin_image = "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png"

st.markdown(
    f"""
    <style>
    .floating-linkedin {{
        position: fixed;
        bottom: 20px; /* Adjust spacing from the bottom */
        left: 20px;   /* Adjust spacing from the left */
        z-index: 100; /* Ensures the widget is above other elements */
    }}
    </style>
    <div class="floating-linkedin">
        <a href="{linkedin_profile}" target="_blank">
            <img src="{linkedin_image}" alt="LinkedIn Profile" width="50">
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

def analyze_audio(file_path):
    """
    Analyze the audio file to detect its key and tuning offset.
    Returns:
      detected_key (str): The estimated key from the audio.
      tuning_offset (float): The estimated tuning offset in cents.
    """
    y, sr = librosa.load(file_path, sr=None)
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    key_index = np.argmax(np.mean(chroma, axis=1))
    detected_key = KEY_NAMES[key_index]
    tuning_offset = librosa.estimate_tuning(y=y, sr=sr) * 100
    return detected_key, tuning_offset

def fix_audio(file_path, desired_key):
    """
    Apply initial pitch shift to correct tuning offset and then apply key switch.
    Returns:
      y_fixed: The processed audio signal.
      sr: The sampling rate.
    """
    y, sr = librosa.load(file_path, sr=None)
    # Detect current key
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    key_index = np.argmax(np.mean(chroma, axis=1))
    detected_key = KEY_NAMES[key_index]
    # Estimate tuning offset (in cents)
    tuning_offset = librosa.estimate_tuning(y=y, sr=sr) * 100
    # Calculate shift: convert tuning offset to semitones (divide by 100) and adjust for desired key
    semitones_shift = - (tuning_offset / 100)
    extra_shift = KEY_NAMES.index(desired_key.upper()) - KEY_NAMES.index(detected_key)
    semitones_shift += extra_shift
    # Apply pitch shift
    y_fixed =pyrb.pitch_shift(y, sr,semitones_shift)
    return y_fixed, sr, semitones_shift

# --- Streamlit App UI ---

st.title("Skanda's Pitch Tuner")

st.markdown("""
This app allows you to:
1. **Upload an audio file.**
2. **Analyze the audio** to detect its key and tuning offset.
3. **Apply a key switch** by selecting a desired key to adjust the audio pitch.
""")

uploaded_file = st.file_uploader("Upload an audio file (wav or mp3)", type=["wav", "mp3"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tfile:
        tfile.write(uploaded_file.read())
        temp_file_path = tfile.name

    st.audio(uploaded_file, format="audio/wav")
    
    if st.button("Analyze Audio"):
        with st.spinner("Analyzing audio..."):
            detected_key, tuning_offset = analyze_audio(temp_file_path)
        st.success("Audio analyzed successfully!")
        st.write(f"**Detected Key:** {detected_key}")
        st.write(f"**Tuning Offset:** {tuning_offset:.2f} cents")

        st.session_state.detected_key = detected_key
        st.session_state.audio_path = temp_file_path

if st.session_state.get("audio_path"):
    st.markdown("---")
    st.subheader("Apply Key Switch")
    default_key = st.session_state.detected_key if "detected_key" in st.session_state else "C"
    desired_key = st.selectbox("Select desired key", KEY_NAMES, index=KEY_NAMES.index(default_key))
    
    if st.button("Fix Audio"):
        cents = 0
        with st.spinner("Fixing audio..."):
            y_fixed, sr, cents =  fix_audio(st.session_state.audio_path, desired_key)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fixed_file:
                sf.write(fixed_file.name, y_fixed, sr)
                fixed_file_path = fixed_file.name
        st.success("Audio fixed!")
        
        st.write(f"Tuned file by {cents*100} cents")
        st.audio(fixed_file_path, format="audio/wav")
        
        with open(fixed_file_path, "rb") as f:
            st.download_button(
                label="Download Fixed Audio",
                data=f,
                file_name="fixed.wav",
                mime="audio/wav"
            )
