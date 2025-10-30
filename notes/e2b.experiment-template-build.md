# Experiment: Membuat template Spring Boot dan menjalankan build (local & E2B)

Dokumen ini merangkum eksperimen untuk:
- Menyediakan template Spring Boot sederhana di repository (`dataset/springboot-demo`)
- Menyajikan editor live (Gradio) yang dapat memuat file template
- Menambahkan alur `Run` yang dapat men-deploy dan menjalankan project baik secara lokal maupun melalui E2B sandbox
- Menyediakan streaming logs ke UI agar mudah debug ketika build / run

Ringkasan perubahan kode
- `dataset/springboot-demo/` - contoh project Spring Boot (pom.xml, Application.java, HelloController.java, target/)
- `scripts/springboot_gradio_editor.py` - Gradio app yang menyediakan:
  - `FileExplorer` terhubung ke `dataset/springboot-demo` untuk memilih file
  - Loader .env sederhana di awal file supaya variabel seperti `E2B_API_KEY` diambil dari `.env`
  - `get_file_content()` yang fallback membaca file dari `dataset/` saat sandbox belum tersedia
  - dua jalur eksekusi:
    - Local stream: `run_local_demo()` — menjalankan `mvn clean package` lalu `java -jar` di folder lokal, streaming stdout/stderr ke UI
    - (Sebelumnya) E2B deploy: `deploy_demo_to_sandbox()` + `build_and_run_application()` — menulis file ke sandbox, menjalankan build di remote
  - Tombol tunggal pada UI: `▶️ Run Demo on E2B` (saat ini wired ke local streaming runner untuk kecepatan dev)

Kontrak singkat (inputs/outputs)
- Input: user menekan tombol Run pada UI
- Output: stream dari status, file tree JSON, preview URL (jika tersedia), dan text log (yang di-render di panel)
- Sukses kondisi: build selesai dengan exit code 0 dan HTTP endpoint `/hello` merespon
- Error mode: kegagalan `mvn`/`java` muncul di log stream; jika E2B key hilang deployment remote tidak dijalankan

Edge cases / catatan penting
- Jika `mvn` atau `java` tidak tersedia pada mesin lokal, jalur lokal akan melaporkan error (ditangkap dan dikirim ke UI)
- E2B sandbox memerlukan `E2B_API_KEY` valid (file `.env` di repo root sudah dimasukkan ke env oleh loader otomatis)
- Menulis ke sandbox bergantung pada API `self.sandbox.files.write` dan `self.sandbox.commands.run` — behaviour ini bergantung pada versi SDK E2B; jika API berbeda, perlu adaptasi (mis. upload archive)
- Build dapat memakan waktu (network, downloads). UI streaming memberi visibility, tapi tetap memerlukan kesabaran.

Prasyarat (local)
- Java 17 (openjdk 17)
- Maven (3.x)
- Virtual environment Python (direkomendasikan) dan dependency Gradio serta `requirements.txt`:
  - Buat venv & install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Pastikan `.env` di root berisi `E2B_API_KEY=...` jika mau gunakan E2B (opsional untuk local)

Cara menjalankan (quick test lokal, recommended untuk development)

1. Aktifkan venv dan jalankan app Gradio:

```bash
source .venv/bin/activate
python scripts/springboot_gradio_editor.py
```

2. Buka UI di browser: http://0.0.0.0:7860
3. Pilih file di `FileExplorer` (dari `dataset/springboot-demo`), edit jika perlu
4. Tekan tombol "▶️ Run Demo on E2B" — saat ini ini menjalankan build+run lokal dan akan men-stream logs ke panel "Application Response".

Jika Anda ingin menjalankan di sandbox E2B
- Pastikan `.env` berisi `E2B_API_KEY` (sudah otomatis dimuat saat skrip diimport)
- Untuk mengaktifkan deployment ke E2B di runtime, kita perlu mengubah wiring tombol kembali ke `run_demo()` yang memanggil `deploy_demo_to_sandbox()` lalu `build_and_run_application()`.
  - Catatan: langkah ini akan mengandalkan API remote E2B yang mungkin berbeda antar versi SDK.

Troubleshooting cepat
- Pesan "❌ E2B_API_KEY not found" di UI: pastikan `.env` ada di root atau export `E2B_API_KEY` sebelum menjalankan skrip.
- Jika `mvn` tidak ditemukan: install Maven atau gunakan Docker/Maven wrapper.
- Jika build lambat: cek jaringan atau coba jalankan `mvn -DskipTests package` langsung di `dataset/springboot-demo` untuk melihat output lengkap.

Next improvements (saran implementasi)
1. Add UI toggle: Local vs E2B run — agar user memilih runtime target tanpa mengubah code.
2. Add abort/stop button to kill running local process or remote sandbox process.
3. Improve sandbox upload: create a single archive (zip/tar) and use sandbox upload API (faster & atomic) instead of per-file writes.
4. Show streaming logs in a nicer tail component (monospace, auto-scroll, color-coded errors).
5. Add status indicator while building (spinner + elapsed time) and disable Run button while active.
6. Add unit/integration smoke tests that run `mvn -q -DskipTests package` in CI to ensure the example builds reproducibly.

Files to inspect
- `scripts/springboot_gradio_editor.py` — utama, lihat functions: `.deploy_demo_to_sandbox()`, `.build_and_run_application()`, `.run_local_demo()`
- `dataset/springboot-demo/` — project template used by the UI
- `.env` — environment variables loader (the script reads file at startup)

Kesimpulan
- Implementasi ini menyediakan alur development cepat: pilih file, tekan Run, lihat streaming logs.
- Untuk produksi (menjalankan di E2B secara remote) diperlukan valid API key dan kemungkinan adaptasi upload sesuai versi E2B SDK.

Jika mau, saya akan:
- Tambahkan toggle Local/E2B di UI sekarang
- Atau ubah label tombol supaya sesuai (mis. "Run Demo (Local)"), dan implementasikan tombol toggle/abort

Pilih salah satu dan saya akan lanjutkan implementasinya.
