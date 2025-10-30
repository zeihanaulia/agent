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

...

## Korelasikan dengan Notebook di Workspace

Notes ini berkorelasi dengan notebook yang ada di workspace untuk demonstrasi praktis penggunaan Hugging Face:

- **[Image Classification](notebooks/image_classification.ipynb)**: Menggunakan pipeline `image-classification` dengan model ViT untuk klasifikasi gambar, sesuai dengan bagian Model Hub dan Transformers Library.
- **[Sentiment Analysis](notebooks/sentiment_analysis.ipynb)**: Menggunakan pipeline `sentiment-analysis` untuk analisis sentimen teks, contoh langsung dari bagian Transformers Library.
- **[Speech Recognition](notebooks/speech_recognition.ipynb)**: Menggunakan pipeline untuk speech-to-text, relevan dengan model seperti Whisper yang disebutkan di Model Hub.
- **[Summarization](notebooks/summarization.ipynb)**: Menggunakan pipeline `summarization` untuk ringkasan teks, bagian dari ekosistem Transformers.
- **[Gradio Sentiment Analysis](gradio/gradio_sentiment_analysis.py)**: Script Python yang mengintegrasikan Gradio untuk UI interaktif, sesuai dengan bagian Gradio Library.
- **[Gradio Image Classification](gradio/gradio_image_classification.py)**: Script Gradio untuk klasifikasi gambar interaktif menggunakan pipeline image-classification.
- **[Gradio Speech Recognition](gradio/gradio_speech_recognition.py)**: Script Gradio untuk transkripsi audio interaktif menggunakan pipeline automatic-speech-recognition.
- **[Gradio Summarization](gradio/gradio_summarization.py)**: Script Gradio untuk ringkasan teks interaktif menggunakan pipeline summarization.

Notebook ini dapat dijalankan untuk melihat implementasi praktis dari konsep yang dijelaskan di atas.
