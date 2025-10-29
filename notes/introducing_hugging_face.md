# Chapter 1 — Introducing Hugging Face

## Ringkasan Umum
Bab ini ngenalin Hugging Face bukan cuma sebagai tempat download model AI, tapi **ekosistem open-source lengkap** buat membangun, melatih, dan menjalankan model machine learning tanpa perlu mulai dari nol.  
Filosofinya: **AI buat semua orang** — lo gak perlu jadi peneliti ML buat bisa manfaatin teknologi mutakhir kayak GPT, BERT, CLIP, atau Whisper.

---

## Apa itu Hugging Face?
Hugging Face adalah komunitas dan platform open-source yang:
- Menyediakan **model AI siap pakai** untuk teks, gambar, dan audio.
- Meng-host lebih dari **1 juta model dan dataset**.
- Mendukung developer untuk **fokus ke solusi**, bukan training dari nol.

Intinya, Hugging Face memungkinkan lo untuk:
> "Menggunakan AI sebagai alat, bukan membangunnya dari awal."

---

## Transformers Library
Transformers adalah **library Python utama** dari Hugging Face.

> *"The Transformers library is a Python package that contains open source implementations of the Transformer architecture models for text, image, and audio tasks. It provides APIs for developers to download and use pretrained models."*

Fungsinya:
- Menyediakan ratusan **model Transformer pretrained** (BERT, GPT, T5, CLIP, Whisper, dll).
- Memiliki API `pipeline()` buat akses cepat tanpa konfigurasi ribet.

### Contoh
```python
from transformers import pipeline

sentiment = pipeline("sentiment-analysis")
result = sentiment("Film ini keren banget!")
print(result)
# [{'label': 'POSITIVE', 'score': 0.9998}]
```

Pipeline ini otomatis download model default (`distilbert-base-uncased-finetuned-sst-2-english`) dan jalan di CPU/GPU lo.

---

## Hugging Face Model Hub

Model Hub adalah **repositori model terbesar di dunia**, tempat lo bisa:

* Menemukan model berdasarkan **task, bahasa, dan arsitektur**.
* Melihat contoh, benchmark, dan dokumentasi lewat *model card*.
* Ngetes model langsung di browser via **Hosted Inference API**.

Contoh model populer:

* `facebook/detr-resnet-50` → object detection
* `google/vit-base-patch16-224` → image classification
* `openai/whisper-base` → speech-to-text

---

## Gradio Library

**Gradio** adalah library Python buat bikin **UI interaktif** dengan cepat.

> "With a few lines of code, you can wrap your model in a web interface where users can upload inputs and view outputs in real time."

### Contoh

```python
import gradio as gr
from transformers import pipeline

sentiment = pipeline("sentiment-analysis")

def analyze(text):
    result = sentiment(text)[0]
    return f"{result['label']} ({result['score']:.2f})"

demo = gr.Interface(fn=analyze, inputs="text", outputs="text", title="Sentiment Analyzer")
demo.launch()
```

Hasilnya: web app lokal buat ngetes model lo tanpa setup frontend.

---

## The Hugging Face Mental Model

Hugging Face punya **alur berpikir 5 langkah** buat nyelesain masalah AI.

### 1. User Need

Mulai dari masalah nyata:

> "Gue pengen tahu review ini positif atau negatif."

### 2. Model Hub Discovery

Cari model yang relevan di Model Hub.
Filter berdasarkan task, arsitektur, bahasa, dan metrik performa.

### 3. Model Card

Pelajari dokumentasi model, contoh pemakaian, dan batasannya.

### 4. Two Execution Paths

* **Path A:** Hosted Inference API → cepat, gak perlu setup.
* **Path B:** Download & run lokal → fleksibel, cocok buat integrasi.

### 5. Results Delivered

Dapatkan hasil dan gunakan di aplikasi lo.

```json
{"label": "POSITIVE", "score": 0.9998}
```

> "Hugging Face isn't just a model repository.
> It's a complete AI pipeline that systematically moves users from problem to solution."

---

## Takeaways

* Hugging Face = **AI ecosystem** (library + hub + UI tools).
* Transformers = **Python SDK** buat akses model pretrained.
* Model Hub = **tempat nyari, ngetes, dan berbagi model.**
* Gradio = **cara cepat bikin UI interaktif** buat model lo.
* Mental Model = **alur berpikir dari masalah → hasil AI.**

---

## Referensi

* *Hugging Face in Action* — Wei-Meng Lee (Manning Publications, 2024)
* [https://huggingface.co/models](https://huggingface.co/models)
* [https://github.com/huggingface/transformers](https://github.com/huggingface/transformers)
* [https://gradio.app](https://gradio.app)

---

## Korelasikan dengan Notebook di Workspace

Notes ini berkorelasi dengan notebook yang ada di workspace untuk demonstrasi praktis penggunaan Hugging Face:

- **[Image Classification](notebooks/image_classification.ipynb)**: Menggunakan pipeline `image-classification` dengan model ViT untuk klasifikasi gambar, sesuai dengan bagian Model Hub dan Transformers Library.
- **[Sentiment Analysis](notebooks/sentiment_analysis.ipynb)**: Menggunakan pipeline `sentiment-analysis` untuk analisis sentimen teks, contoh langsung dari bagian Transformers Library.
- **[Speech Recognition](notebooks/speech_recognition.ipynb)**: Menggunakan pipeline untuk speech-to-text, relevan dengan model seperti Whisper yang disebutkan di Model Hub.
- **[Summarization](notebooks/summarization.ipynb)**: Menggunakan pipeline `summarization` untuk ringkasan teks, bagian dari ekosistem Transformers.
- **[Gradio Sentiment Analysis](scripts/gradio_sentiment_analysis.py)**: Script Python yang mengintegrasikan Gradio untuk UI interaktif, sesuai dengan bagian Gradio Library.
- **[Gradio Image Classification](scripts/gradio_image_classification.py)**: Script Gradio untuk klasifikasi gambar interaktif menggunakan pipeline image-classification.
- **[Gradio Speech Recognition](scripts/gradio_speech_recognition.py)**: Script Gradio untuk transkripsi audio interaktif menggunakan pipeline automatic-speech-recognition.
- **[Gradio Summarization](scripts/gradio_summarization.py)**: Script Gradio untuk ringkasan teks interaktif menggunakan pipeline summarization.

Notebook ini dapat dijalankan untuk melihat implementasi praktis dari konsep yang dijelaskan di atas.

