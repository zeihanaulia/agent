import gradio as gr
from transformers import pipeline

sentiment = pipeline("sentiment-analysis") # pyright: ignore[reportArgumentType, reportCallIssue]

def analyze(text):
    result = sentiment(text)[0]
    return f"{result['label']} ({result['score']:.2f})"

demo = gr.Interface(fn=analyze, inputs="text", outputs="text", title="Sentiment Analyzer")
demo.launch()
