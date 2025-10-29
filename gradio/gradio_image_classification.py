import gradio as gr
from transformers import pipeline
from PIL import Image

# Load the image classification pipeline
classifier = pipeline("image-classification", model="google/vit-base-patch16-224")

def classify_image(image):
    """
    Classify the uploaded image and return top predictions.
    """
    if image is None:
        return "Please upload an image."

    # If image is a file path (from upload), open it
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image  # Assuming it's already a PIL Image

    # Perform classification
    results = classifier(img)

    # Format results
    output = "Top predictions:\n"
    for i, result in enumerate(results[:5], 1):  # Top 5 predictions
        label = result['label']
        score = result['score']
        output += f"{i}. {label}: {score:.4f}\n"

    return output

# Create Gradio interface
demo = gr.Interface(
    fn=classify_image,
    inputs=gr.Image(type="pil", label="Upload Image"),
    outputs=gr.Textbox(label="Classification Results"),
    title="Image Classification with ViT",
    description="Upload an image to classify it using Vision Transformer (ViT) model."
)

if __name__ == "__main__":
    demo.launch()