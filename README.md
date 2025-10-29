# AI Research Agent

Proyek ini berisi berbagai notebook dan script untuk eksperimen dengan AI menggunakan Hugging Face, termasuk klasifikasi gambar, analisis sentimen, pengenalan suara, dan ringkasan teks.

## Daftar Notebook dan Script

1. **Image Classification**  
   - [Notebook](notebooks/image_classification.ipynb): Demonstrasi klasifikasi gambar menggunakan Vision Transformer (ViT).  
   - [Gradio Script](scripts/gradio_image_classification.py): UI interaktif untuk klasifikasi gambar.

2. **Sentiment Analysis**  
   - [Notebook](notebooks/sentiment_analysis.ipynb): Analisis sentimen teks menggunakan pipeline sentiment-analysis.  
   - [Gradio Script](scripts/gradio_sentiment_analysis.py): UI interaktif untuk analisis sentimen.

3. **Speech Recognition**  
   - [Notebook](notebooks/speech_recognition.ipynb): Konversi speech-to-text menggunakan model seperti Whisper.  
   - [Gradio Script](scripts/gradio_speech_recognition.py): UI interaktif untuk transkripsi audio.

4. **Summarization**  
   - [Notebook](notebooks/summarization.ipynb): Ringkasan teks menggunakan model BART.  
   - [Gradio Script](scripts/gradio_summarization.py): UI interaktif untuk ringkasan teks.

5. **GPU Device Detection**  
   - [Notebook](notebooks/gpu_device_notebook.ipynb): Demonstrasi deteksi perangkat GPU dan sentiment analysis dengan device selection.  
   - [Gradio Script](scripts/gradio_device_sentiment.py): UI interaktif untuk sentiment analysis dengan auto device detection.

6. **E2B Code Runner**  
   - [Python Script](e2b_sandbox_runner.py): Implementasi lengkap E2B learning steps untuk sandbox management.  
   - [Interactive Notebook](notebooks/e2b_sandbox_runner.ipynb): Notebook Jupyter interaktif untuk pembelajaran E2B sandbox.  
   - [Gradio Script](scripts/gradio_e2b_code_runner.py): UI interaktif seperti Replit untuk coding dan running code di E2B sandbox.

7. **Code Repair Agent**  
   - [Gradio Script](scripts/gradio_code_repair_agent.py): AI agent yang menggunakan E2B sandbox untuk debugging dan memperbaiki kode secara iteratif.

8. **Spring Boot Live Editor**
   - [Notes / Experiment](notes/experiment-template-build.md): Catatan eksperimen membuat template Spring Boot dan alur build/run.
   - [Gradio Script](scripts/springboot_gradio_editor.py): Live code editor dengan FileExplorer, Run button, dan streaming build logs (local / E2B).
   - `dataset/springboot-demo/`: Contoh project Spring Boot yang digunakan sebagai template (pom.xml, Application.java, HelloController.java).

## Notes

- **[Introducing Hugging Face](notes/introducing_hugging_face.md)**  
  Catatan lengkap tentang ekosistem Hugging Face, termasuk Transformers Library, Model Hub, dan Gradio.

- **[Introducing E2B Sandbox](notes/introducing_e2b_sandbox.md)**  
  Catatan lengkap tentang E2B (Execute Code in Browser), compute layer untuk AI agents dengan sandbox terisolasi, termasuk implementasi praktis dan best practices.

## Requirements

Install dependencies dengan:
```
pip install -r requirements.txt
```

**Untuk fitur E2B (Code Runner & Code Repair Agent):**
```
pip install e2b e2b-code-interpreter
```

Dan pastikan environment variable `E2B_API_KEY` sudah diset:
```bash
export E2B_API_KEY="your_api_key_here"
```
Dapatkan API key dari: https://e2b.dev/dashboard

Direkomendasikan environment:

- Python 3.10 atau lebih baru.
- Buat dan aktifkan virtual environment sebelum instalasi:
   - python -m venv .venv
   - source .venv/bin/activate  # macOS / Linux (zsh)
   - .\\.venv\\Scripts\\activate  # Windows (PowerShell/CMD)

Catatan: jika `requirements.txt` tidak mem-pin versi paket penting (mis. `transformers`, `torch`), pertimbangkan untuk menyematkan versi paket agar lebih reproducible.

## Cara Menjalankan

1. Aktivasi virtual environment (jika ada): `source .venv/bin/activate`
2. Jalankan notebook dengan Jupyter: `jupyter notebook`
3. Atau jalankan script Python langsung.

Contoh menjalankan skrip Gradio (misal untuk klasifikasi gambar):

```
python scripts/gradio_image_classification.py
```

Contoh menjalankan E2B scripts:

```
# E2B Code Runner (seperti Replit)
python scripts/gradio_e2b_code_runner.py

# E2B Code Repair Agent (AI yang auto fix code)
python scripts/gradio_code_repair_agent.py

# E2B Learning Script (command line)
python e2b_sandbox_runner.py
```

Biasanya Gradio akan membuka UI di http://127.0.0.1:7860 kecuali dinyatakan lain di skrip.

### Model Download
Saat menjalankan notebook atau script Gradio untuk pertama kali, model AI akan otomatis didownload dari Hugging Face Hub. Model disimpan di direktori cache lokal (`~/.cache/huggingface/hub/`) untuk penggunaan selanjutnya.

### Cleanup Model Cache
Untuk membersihkan model yang telah didownload dan mengosongkan ruang disk:
- Hapus cache folder secara manual: `rm -rf ~/.cache/huggingface/hub/`
- Untuk melihat ukuran cache: `du -sh ~/.cache/huggingface/`

**Catatan:** Model akan didownload ulang saat diperlukan jika cache dihapus.

Catatan HF token / rate limits:
- Jika Anda mengakses model private atau ingin mengurangi kemungkinan terkena rate limit, set environment variable `HF_TOKEN` sebelum menjalankan skrip/notebook:
   - export HF_TOKEN="hf_xxx..."
   - Lihat https://huggingface.co/settings/tokens untuk membuat token.

## Troubleshooting (singkat)
- Model download gagal: periksa koneksi, ruang disk, dan permission pada `~/.cache/huggingface/`.
- Masalah CUDA / GPU: pastikan versi `torch` kompatibel dengan CUDA di mesin Anda. Pada macOS tanpa CUDA gunakan versi CPU dari `torch`.
- Jika notebook memerlukan banyak memori/GPU: gunakan model lebih kecil (distilled) atau jalankan di CPU untuk pengujian ringan.
- Rate limit dari Hugging Face: gunakan `HF_TOKEN` atau model yang sudah dicache.
- **E2B Issues**: Pastikan `E2B_API_KEY` sudah diset dengan benar. Jika mendapat error koneksi, periksa internet connection dan API key validity.

## Kontribusi & Lisensi (opsional)
- Jika repo akan dibagikan publik, pertimbangkan menambahkan file `LICENSE` dan `CONTRIBUTING.md`.

---
Ringkasan perubahan: menambah rekomendasi Python/venv, catatan HF_TOKEN, contoh menjalankan Gradio, troubleshooting singkat, dan penambahan fitur E2B (Code Runner, Code Repair Agent, dan dokumentasi lengkap).

## Referensi

- [Hugging Face Models](https://huggingface.co/models)
- [Transformers Library](https://github.com/huggingface/transformers)
- [Gradio](https://gradio.app)
- [E2B Documentation](https://e2b.dev/docs)
- [E2B Dashboard](https://e2b.dev/dashboard)