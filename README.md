
# AI Research Agent

Proyek ini berisi notebook, script, dan eksperimen untuk eksplorasi model dan agen (Hugging Face, Gradio, E2B, Deep Agents).

## Daftar Notebook & Script

1. **Image Classification**
   - Notebook: [notebooks/image_classification.ipynb](notebooks/image_classification.ipynb) — klasifikasi gambar (ViT).
   - Gradio: [gradio/gradio_image_classification.py](gradio/gradio_image_classification.py)

2. **Sentiment Analysis**
   - Notebook: [notebooks/sentiment_analysis.ipynb](notebooks/sentiment_analysis.ipynb) — analisis sentimen.
   - Gradio: [gradio/gradio_sentiment_analysis.py](gradio/gradio_sentiment_analysis.py)

3. **Speech Recognition**
   - Notebook: [notebooks/speech_recognition.ipynb](notebooks/speech_recognition.ipynb) — speech-to-text (Whisper).
   - Gradio: [gradio/gradio_speech_recognition.py](gradio/gradio_speech_recognition.py)

4. **Summarization**
   - Notebook: [notebooks/summarization.ipynb](notebooks/summarization.ipynb) — ringkasan teks.
   - Gradio: [gradio/gradio_summarization.py](gradio/gradio_summarization.py)

5. **GPU Device Detection**
   - Notebook: [notebooks/gpu_device_notebook.ipynb](notebooks/gpu_device_notebook.ipynb) — demo deteksi device.
   - Gradio: [gradio/gradio_device_sentiment.py](gradio/gradio_device_sentiment.py)

6. **E2B Code Runner**
   - Script: [e2b_sandbox_runner.py](e2b_sandbox_runner.py)
   - Notebook: [notebooks/e2b_sandbox_runner.ipynb](notebooks/e2b_sandbox_runner.ipynb)
   - Gradio: [gradio/gradio_e2b_code_runner.py](gradio/gradio_e2b_code_runner.py)

7. **Code Repair Agent**
   - Gradio: [gradio/gradio_code_repair_agent.py](gradio/gradio_code_repair_agent.py)

8. **Spring Boot Live Editor**
   - Notes: [notes/experiment-template-build.md](notes/experiment-template-build.md)
   - Notes: [notes/springboot_gradio_sandbox_preview_experiment.md](notes/springboot_gradio_sandbox_preview_experiment.md)
    - Notes: [notes/e2b.experiment-template-build.md](notes/e2b.experiment-template-build.md)
    - Notes: [notes/e2b.springboot_gradio_sandbox_preview_experiment.md](notes/e2b.springboot_gradio_sandbox_preview_experiment.md)
   - Gradio: [gradio/gradio_springboot_generator.py](gradio/gradio_springboot_generator.py)
   - Example project: [dataset/springboot-demo/](dataset/springboot-demo/)

9. **Deep Agents Experiments**
   - Gradio: [gradio/gradio_deepagent_experiments.py](gradio/gradio_deepagent_experiments.py) — eksperimen agen (basic, planning, subagents, filesystem, parallel) dengan streaming log.

## TODO / Coding-agent baseline

Rencana awal untuk coding-agent: "generate → build → test → repair" otomatis.

- Reusable components: [notes/springboot_gradio_sandbox_preview_experiment.md](notes/springboot_gradio_sandbox_preview_experiment.md).
 - Reusable components: [notes/e2b.springboot_gradio_sandbox_preview_experiment.md](notes/e2b.springboot_gradio_sandbox_preview_experiment.md).
- Target awal:
  - Persistent build sandbox (cache `~/.m2`).
  - `build_and_test_once(sandbox, project_dir)` mengembalikan struktur hasil (success, logs, errors, artifact_path).
  - Parser sederhana untuk mengekstrak error kompilasi dari output Maven.
  - Repair loop API: jalankan build → kirim errors ke agent → terapkan patch → ulangi.

Jika mau, saya bisa mulai mengimplementasikan helper module untuk ini.

## Notes

Berikut catatan dan eksperimen di folder `notes/`, dikelompokkan per topik. Jika ingin saya ubah nama file (prefix seperti `e2b.` / `huggingface.` / `deepagents.`) beri tahu dan saya akan melakukan rename + update tautan.

### Code Analysis (filesystem backend & agent implementation)

1. [Code Analysis Guide](notes/codeanalysis.guide.md) — Panduan lengkap untuk code analysis agent dengan FilesystemBackend.
2. [Filesystem Backend Index](notes/codeanalysis.filesystem-backend-index.md) — Daftar lengkap dokumentasi FilesystemBackend implementation.
3. [Filesystem Backend Implementation Guide](notes/codeanalysis.filesystem-backend-implementation-guide.md) — Panduan implementasi FilesystemBackend dari awal.
4. [Filesystem Backend Migration Summary](notes/codeanalysis.filesystem-backend-migration-summary.md) — Ringkasan migrasi dari custom tools ke FilesystemBackend.
5. [Filesystem Backend Quick Reference](notes/codeanalysis.filesystem-backend-quick-reference.md) — Referensi cepat untuk FilesystemBackend API dan tools.
6. [Filesystem Backend Summary](notes/codeanalysis.filesystem-backend-summary.md) — Ringkasan implementasi dan hasil testing FilesystemBackend.
7. [Filesystem Backend Temperature Bugfix](notes/codeanalysis.filesystem-backend-temperature-bugfix.md) — Dokumentasi perbaikan bug temperature compatibility.
8. [Filesystem Backend Debugging](notes/codeanalysis.filesystem-backend-debugging.md) — Catatan debugging dan troubleshooting FilesystemBackend.
9. [Filesystem Backend Resolution](notes/codeanalysis.filesystem-backend-resolution.md) — Resolusi masalah dan solusi yang diterapkan.
10. [Filesystem Backend Files Created](notes/codeanalysis.filesystem-backend-files-created.md) — Daftar file dokumentasi yang dibuat selama implementasi.
11. [Filesystem Backend Pending Fix](notes/codeanalysis.filesystem-backend-pending-fix.md) — Catatan masalah yang masih pending (jika ada).
12. [Filesystem Backend Comparison](notes/codeanalysis.filesystem-backend-comparison.md) — Perbandingan FilesystemBackend vs custom tools.
13. [Builtin vs Custom Tools Comparison](notes/builtin-vs-custom-tools-comparison.md) — Analisis perbandingan tools built-in vs custom.
14. [CodeAnalysis: Builtin vs Custom Tools](notes/codeanalysis.builtin-vs-custom-tools-comparison.md) — Perbandingan spesifik untuk code analysis tools.

### E2B (sandbox / execution)

1. [Introducing E2B Sandbox](notes/e2b.introducing_e2b_sandbox.md) — Panduan E2B: lifecycle sandbox, templates, streaming execution.
2. [Experiment: Membuat template Spring Boot dan menjalankan build](notes/e2b.experiment-template-build.md) — Membuat template Spring Boot dan alur build/run.
3. [Spring Boot + E2B Sandbox + Gradio Preview (experiment)](notes/e2b.springboot_gradio_sandbox_preview_experiment.md) — Live preview & streaming build logs (Spring Boot + E2B + Gradio).

### Hugging Face (models & Gradio)

1. [Introducing Hugging Face](notes/huggingface.introducing_hugging_face.md) — Intro ke Transformers, model hub, dan contoh Gradio UIs.

### Deep Agents (agent architecture & experiments)

1. [Deep Agents: Introduction & Learning Notes](notes/deepagents.deep_agents_notes.md) — Catatan arsitektur Deep Agents: planning, subagents, filesystem middleware, eksperimen.

## Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

Untuk fitur E2B (Code Runner & Code Repair Agent):
```bash
pip install e2b e2b-code-interpreter
export E2B_API_KEY="your_api_key_here"
```

Direkomendasikan: Python 3.10+. Buat virtualenv sebelum instalasi:
```bash
python -m venv .venv
source .venv/bin/activate
```

## Cara Menjalankan

1. Aktifkan virtualenv (jika ada): `source .venv/bin/activate`
2. Jalankan notebook atau skrip Gradio. Contoh Gradio:

```bash
python gradio/gradio_image_classification.py
python gradio/gradio_e2b_code_runner.py
python gradio/gradio_code_repair_agent.py
python gradio/gradio_deepagent_experiments.py
```

Gradio biasanya tersedia di http://127.0.0.1:7860

## Model Download & Cache

Model yang digunakan otomatis didownload ke `~/.cache/huggingface/hub/`.
Hapus cache jika perlu: `rm -rf ~/.cache/huggingface/hub/`

Set `HF_TOKEN` jika akses model private atau ingin mengurangi rate limits:
```bash
export HF_TOKEN="hf_xxx"
```

## Troubleshooting (singkat)

- Model download gagal: periksa koneksi dan disk.
- CUDA/GPU issues: pastikan versi `torch` kompatibel atau gunakan CPU build di macOS.
- E2B: pastikan `E2B_API_KEY` benar.

## Kontribusi & Lisensi

Pertimbangkan menambahkan `LICENSE` dan `CONTRIBUTING.md` jika repo akan dibagikan publik.
