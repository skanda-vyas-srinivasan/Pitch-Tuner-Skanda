import streamlit as st
import requests
from io import BytesIO

backgroundColor = "#121212"
# URL where the Flask API is running
API_URL = "http://localhost:5000"


st.title("Skanda's Pitch Tuner")

st.markdown("""
This app allows you to:
1. **Upload an audio file.**
2. **Analyze the audio** to detect its key and tuning offset.
3. **Apply a key switch** by selecting a desired key to adjust the audio pitch.
""")

# Step 1: Upload the audio file
uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3"])

if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/wav")
    
    # Analyze button: Send the audio file to the Flask API
    if st.button("Analyze Audio"):
        # Prepare the file for the request (reset pointer and create a tuple)
        uploaded_file.seek(0)
        files = {
            'file': (uploaded_file.name, uploaded_file, uploaded_file.type)
        }
        with st.spinner("Analyzing audio..."):
            response = requests.post(f"{API_URL}/analyze", files=files)
        if response.status_code == 200:
            data = response.json()
            detected_key = data.get("key")
            tuning_offset = data.get("tuning_offset")
            st.success("Audio analyzed successfully!")
            st.write(f"**Detected Key:** {detected_key}")
            st.write(f"**Tuning Offset:** {tuning_offset} cents")
            
            # Store detected values in session state for later use.
            st.session_state.detected_key = detected_key
            st.session_state.tuning_offset = tuning_offset
            st.session_state.audio_uploaded = True
        else:
            st.error("Error analyzing audio: " + response.text)

# Step 2: If audio has been analyzed, let the user choose a desired key
if st.session_state.get("audio_uploaded", False):
    st.markdown("---")
    st.subheader("Apply Key Switch")
    desired_key = st.selectbox(
        "Select desired key",
        ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    )
    
    if st.button("Apply Key Switch"):
        # Post desired_key as form data to the Flask endpoint
        data = {'desired_key': desired_key}
        with st.spinner("Processing audio..."):
            response = requests.post(f"{API_URL}/key_switch", data=data)
        if response.status_code == 200:
            st.success("Key switch applied successfully!")
            # Get the processed audio file as bytes
            processed_audio = BytesIO(response.content)
            
            # Provide an audio player for the result
            st.audio(processed_audio, format="audio/wav")
            
            # Reset the pointer for download button
            processed_audio.seek(0)
            st.download_button(
                label="Download Processed Audio",
                data=processed_audio,
                file_name="fixed.wav",
                mime="audio/wav"
            )
        else:
            st.error("Error applying key switch: " + response.text)
