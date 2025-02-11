from flask import Flask, request, jsonify, send_file
import librosa
import librosa.effects
import numpy as np
import soundfile as sf
import tempfile
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

tuning_offset = -np.inf
audio_data = None
sample_rate = None
detected_key = None
key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

@app.route('/analyze', methods=['POST'])
def process_audio():
    global detected_key,  tuning_offset, audio_data, sample_rate
    print("Received files:", list(request.files.keys()))
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400
    
    print("Error Not here")

    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    file.save(temp_input.name)
    temp_input.close()

    print("file saved to a temp")

    y, sr = librosa.load(temp_input.name, sr=None)
    
    audio_data = y
    sample_rate = sr
    key_estimation = librosa.feature.chroma_cens(y=y, sr=sr)
    key_index = np.argmax(np.mean(key_estimation, axis=1))
    detected_key = key_names[key_index]

    tuning_offset = librosa.estimate_tuning(y=y, sr=sr) * 100

    print("Detected key:", detected_key)
    print("Tuning offset:", tuning_offset)

    return jsonify({'key': detected_key, 'tuning_offset': tuning_offset})

@app.route('/key_switch', methods=['POST'])
def work_it():

    if(tuning_offset==-np.inf or detected_key==None):
        return jsonify({'error': 'No file analyzed yet.'}), 400

    desired_key = request.form.get('desired_key', None)
    if desired_key is None or desired_key.upper() not in key_names:
        return jsonify({'error': 'Invalid or missing desired key.'}), 400
    

    semitones_shift = - (tuning_offset / 100)
    extra_shift = key_names.index(desired_key.upper()) - key_names.index(detected_key)
    semitones_shift += extra_shift

    y_fixed = librosa.effects.pitch_shift(y=audio_data, sr=sample_rate, n_steps=semitones_shift, res_type='kaiser_best')

    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    sf.write(temp_output.name, y_fixed, sample_rate)
    temp_output.close()
    print("Dude the output closed as well")
    return send_file(temp_output.name, as_attachment=True, download_name="fixed.wav", mimetype="audio/wav")



if __name__ == "__main__":
    app.run(debug=True)
