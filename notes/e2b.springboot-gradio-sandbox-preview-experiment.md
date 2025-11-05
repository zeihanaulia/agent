## Eksperimen: Spring Boot + E2B Sandbox + Gradio Preview

Tanggal: 2025-10-29

Ringkasan singkat
-----------------
Percobaan ini membuat sebuah developer tool yang otomatis:
- Meng-upload project Spring Boot ke E2B sandbox.
- Membangun project (mvn clean package -DskipTests) dan men-stream output build ke UI.
- Menjalankan JAR di background (nohup java -jar ...) dan men-stream log startup.
- Menyediakan preview (iframe) dari hostname sandbox agar pengguna dapat membuka aplikasi yang berjalan.

Dokumen ini merangkum implementasi, hasil, masalah yang ditemui, dan komponen yang bisa dipakai ulang sebagai baseline untuk coding-agent (generate → build → test → repair loop).

Lokasi file utama
-----------------
- `gradio/gradio_springboot_generator.py` — demo Gradio. Kode penting:
  - build_and_stream(...)  — streaming build logs ke UI
  - start_app_and_test(...) — jalankan jar, chunked-tail log startup, deteksi readiness
  - run_app_and_preview(...) / stop_preview(...) — persistent preview sandbox + iframe
  - PREVIEW_SANDBOX — variabel module-level yang menyimpan sandbox preview (jika aktif)
- `scripts/springboot_generator.py` — script referensi (baseline kecepatan, non-Gradio).
- `dataset/springboot-demo/` — contoh project Spring Boot (pom.xml, Application.java, HelloController.java).

Asumsi lingkungan
-----------------
- Python 3.12, virtualenv (.venv), Gradio Blocks API.
- E2B sandbox API tersedia dan menyediakan: `create`, `commands.run(..., on_stdout=..., on_stderr=..., timeout=...)`, `files.write(...)`, `kill()`, dan `get_host(port)`.
- Tool di sandbox: `mvn`, `java`, `nohup`, `tail`, `ps`, `netstat`/`ss`, `curl`.

Langkah implementasi (ringkas)
-----------------------------
1. UI: layout dua kolom — kiri file viewer, kanan kontrol (Build, Start & Test, Run Preview, Stop) dan area logs.
2. Build streaming (`build_and_stream`): upload file → jalankan `mvn clean package -DskipTests` dengan callback streaming ke Gradio.
3. Start + readiness detection (`start_app_and_test`): jalankan `nohup java -jar target/*.jar > app.log 2>&1 &`, lalu lakukan chunked-tail (`tail -n 0 -f app.log`) dalam loop pendek (mis. 4s) sambil mengecek:
   - Java process via `ps`.
   - Port 8080 listening via `netstat`/`ss`.
   - Pola teks di log seperti "Started" atau "Tomcat started".
   Jika terdeteksi, fungsi melepaskan (detach) stream agar generator lanjut dan app tetap berjalan.
4. Persistent preview (`run_app_and_preview` / `stop_preview`): buat/reuse sandbox, build, jalankan jar (dengan `echo $!` bila tersedia untuk PID), dan tampilkan iframe berisi `sandbox.get_host(port=8080)`; simpan sandbox di `PREVIEW_SANDBOX` agar user bisa menghentikannya manual.

Masalah yang ditemui dan solusi
-------------------------------
- Gradio binding error: "Cannot call change outside of a gradio.Blocks context" — solusi: buat semua `.change`/`.click` di dalam konteks `with gr.Blocks(...)` dan pastikan komponen target sudah didefinisikan sebelum wiring.
- Duplicate/verbose log printing saat startup — penyebab: `tail -n +1 -f` reprints file; solusi: `tail -n 0 -f` + chunked timeouts agar hanya baris baru yang diambil.
- Preview tidak terlihat di dark mode — solusi: set wrapper dan iframe background putih.
- Build lambat tiap run — penyebab: sandbox baru per run (tidak ada cache `~/.m2`); rekomendasi: reuse sandbox / persist Maven cache.

Reusable components (langsung bisa dipakai oleh coding-agent)
---------------------------------------------------------
Berikut fungsi/komponen yang sudah ada dan cocok dipakai ulang sebagai baseline untuk agen pengkodean (generate → build → test → repair):

- `gradio/gradio_springboot_generator.py::build_and_stream(sandbox, project_dir, ...)`
  - Tujuan: jalankan `mvn clean package -DskipTests` dan stream output build ke UI. Agen dapat memanggil ini untuk mendapatkan log build.

- `gradio/gradio_springboot_generator.py::start_app_and_test(sandbox, project_dir, ...)`
  - Tujuan: jalankan jar di background, stream startup log secara chunked, dan lakukan readiness checks (process, port, log patterns). Mengembalikan hasil readiness dan output curl endpoint sederhana.

- `gradio/gradio_springboot_generator.py::run_app_and_preview()` dan `stop_preview()`
  - Tujuan: buat/reuse sandbox untuk preview, jalankan app, dan tampilkan iframe `sandbox.get_host(port=8080)`. `stop_preview()` menghentikan sandbox preview.

- `PREVIEW_SANDBOX` (module-level variable)
  - Menyimpan sandbox preview yang sedang berjalan jika ingin persist preview di antara iterasi.

... (content truncated, identical to original)
