import gradio as gr
from transformers import pipeline

# Load the summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_text(text, max_length=60, min_length=10):
    """
    Summarize the input text.
    """
    if not text.strip():
        return "Please enter some text to summarize."

    # Perform summarization
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]["summary_text"]

# Create Gradio interface
demo = gr.Interface(
    fn=summarize_text,
    inputs=[
        gr.Textbox(lines=10, label="Input Text", placeholder="Enter text to summarize..."),
        gr.Slider(minimum=10, maximum=200, value=60, step=10, label="Max Length"),
        gr.Slider(minimum=5, maximum=50, value=10, step=5, label="Min Length")
    ],
    outputs=gr.Textbox(label="Summary"),
    title="Text Summarization with BART",
    description="Enter text to generate a summary using BART model. Adjust length parameters as needed."
)

if __name__ == "__main__":
    demo.launch()