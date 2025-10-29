import gradio as gr
import torch
from transformers import pipeline

def get_device():
    """Get the best available device for inference."""
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    return device

def analyze_sentiment(text):
    """Analyze sentiment of input text."""
    device = get_device()

    # Create pipeline with device
    classifier = pipeline(
        "text-classification",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        device=device
    )

    result = classifier(text)[0]
    return f"Device: {device.upper()}\nLabel: {result['label']}\nConfidence: {result['score']:.4f}"

def get_device_info():
    """Get detailed device information."""
    device = get_device()
    info = f"Current device: {device}\n"

    if torch.cuda.is_available():
        info += f"CUDA devices: {torch.cuda.device_count()}\n"
        info += f"CUDA device name: {torch.cuda.get_device_name(0)}\n"
        info += f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory/1e9:.2f} GB\n"
    elif torch.backends.mps.is_available():
        info += "Apple Silicon MPS is available\n"
    else:
        info += "Using CPU\n"

    return info

# Create Gradio interface with Blocks for more control
with gr.Blocks(title="Device-Aware Sentiment Analysis") as demo:
    gr.Markdown("# Device-Aware Sentiment Analysis with Hugging Face")
    gr.Markdown("This app automatically detects and uses the best available device (CUDA/MPS/CPU) for sentiment analysis.")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="Enter text for sentiment analysis",
                placeholder="Type your text here...",
                lines=3
            )
            analyze_btn = gr.Button("Analyze Sentiment")

        with gr.Column():
            device_info = gr.Textbox(
                label="Device Information",
                value=get_device_info(),
                interactive=False,
                lines=5
            )

    output = gr.Textbox(label="Sentiment Analysis Result")

    analyze_btn.click(
        fn=analyze_sentiment,
        inputs=text_input,
        outputs=output
    )

    gr.Markdown("""
    ## How it works:
    - **Automatic Device Detection**: The app detects CUDA (NVIDIA GPUs), MPS (Apple Silicon), or falls back to CPU
    - **Optimized Performance**: Models run on the fastest available hardware
    - **Sentiment Analysis**: Uses DistilBERT fine-tuned on SST-2 dataset

    ## Device Comparison:
    - **CUDA**: NVIDIA GPU acceleration (most common in ML)
    - **MPS**: Apple Silicon GPU acceleration (Mac M1/M2/M3 chips)
    - **CPU**: Fallback option, works everywhere but slower
    """)

if __name__ == "__main__":
    demo.launch()