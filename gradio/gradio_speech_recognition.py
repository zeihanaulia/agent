import gradio as gr
from transformers import pipeline

def create_asr_pipeline(language="auto"):
    """
    Create ASR pipeline with specified language.
    """
    if language == "auto":
        return pipeline("automatic-speech-recognition", model="openai/whisper-base")
    else:
        return pipeline("automatic-speech-recognition", model="openai/whisper-base",
                       generate_kwargs={"task": "transcribe", "language": language})

def transcribe_audio(audio, language):
    """
    Transcribe the uploaded audio file.
    """
    if audio is None:
        return "Please upload an audio file."

    # Create pipeline based on language
    asr = create_asr_pipeline(language)

    # Transcribe
    result = asr(audio)
    return result["text"]

# Create Gradio interface
demo = gr.Interface(
    fn=transcribe_audio,
    inputs=[
        gr.Audio(type="filepath", label="Upload Audio File"),
        gr.Dropdown(choices=["auto", "en", "id", "es", "fr"], value="auto", label="Language")
    ],
    outputs=gr.Textbox(label="Transcription"),
    title="Speech Recognition with Whisper",
    description="Upload an audio file to transcribe it using OpenAI Whisper model. Choose language or auto-detect."
)

if __name__ == "__main__":
    demo.launch()