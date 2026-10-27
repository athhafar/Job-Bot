# 📱 Mobile Job Opportunity Bot (Flutter • Android Kotlin • React Native)

> **Bot Pemantau Peluang & Lowongan Mobile Development Otomatis (Rp0)**
> Memantau job board, Reddit, dan Hacker News secara berkala via **GitHub Actions (Gratis)**, memfilter postingan dengan keyword cerdas, lalu menggunakan **Google Gemini API** untuk menilai relevansi serta membuatkan **DRAFT Balasan (Komentar & DM)** yang siap dikirim langsung ke **Telegram** Anda.

---

## 🎯 Mengapa Bot Ini Dibuat?

Sebagai mobile developer, mendapatkan proyek atau pekerjaan freelance/remote seringkali ditentukan oleh **kecepatan merespons**:
- ❌ **Masalah**: Scroll manual r/forhire, RemoteOK, dan Hacker News membuang waktu berjam-jam, sering terlambat karena postingan sudah ditumpuk puluhan pelamar lain.
- ❌ **Bot Biasa yang Buruk**: Melakukan auto-DM / auto-spam yang melanggar ToS platform, merusak reputasi Anda, dan sering ditolak klien.
- ✅ **Solusi Bot Ini**: **Review Manusia (Human-in-the-Loop)**. Bot hanya memberi notifikasi instan ke HP Anda lewat Telegram lengkap dengan:
  1. Ringkasan singkat lowongan & skor relevansi (1-10).
  2. Tautan langsung ke postingan asli.
  3. **Draft komentar publik** (maks 2 kalimat, sopan, pamer skill relevan, ajak DM).
  4. **Draft DM personal** (maks 5 kalimat, tailored berdasarkan portofolio di `config/profile.md`).
  5. Teks draft ditaruh di dalam tag `<code>` sehingga Anda cukup **sekali tap di layar HP untuk copy**, lalu kirim sendiri secara manual!

---

## 🏗️ Struktur Proyek

```text
├── main.py                  # Entry point orchestrator pipeline bot
├── config.yaml              # Konfigurasi keyword, sumber data, limit & setting
├── config/
│   └── profile.md           # Profil & portofolio Anda (dibaca oleh Gemini)
├── prompts/
│   └── draft.txt            # System prompt & aturan penulisan balasan AI
├── sources/                 # Modul sumber data modular (fetch() -> List[JobItem])
│   ├── base.py              # Definisi JobItem & BaseSource
│   ├── rss.py               # RemoteOK, We Work Remotely, Himalayas RSS
│   ├── reddit.py            # Reddit public JSON/RSS (r/forhire, r/FlutterDev, dll)
│   ├── hn.py                # Hacker News "Who is hiring" via Algolia API
│   └── threads_stub.py      # Stub Meta Threads API & Telegram Channel
├── core/
│   ├── filters.py           # Filter kata kunci, umur post, dan deduplikasi
│   ├── gemini_client.py     # Gemini API client, auto retry 429, fallback template
│   ├── notifier.py          # Telegram sender (HTML format, inline buttons, alerts)
│   └── storage.py           # Manajemen state seen.json (max 5000 item)
├── tests/                   # Unit test otomatis (pytest)
│   ├── test_filters.py      # Uji logika filter & deduplikasi
│   └── test_gemini.py       # Uji parsing JSON & fallback template
├── seen.json                # Database sederhana ID yang sudah dikirim
├── requirements.txt         # Dependensi Python minimal (requests, feedparser, dll)
├── .env.example             # Contoh environment variables lokal
├── .github/
│   └── workflows/
│       └── bot.yml          # GitHub Actions cron setiap 20 menit (GRATIS)
└── README.md                # Dokumentasi lengkap panduan setup
```

---

## 🚀 Panduan Setup Lengkap dari Nol (Langkah Demi Langkah)

### Langkah 1: Dapatkan Gemini API Key Gratis
1. Buka [Google AI Studio](https://aistudio.google.com/).
2. Login menggunakan akun Google Anda.
3. Klik tombol **Get API key** di pojok kiri atas.
4. Klik **Create API key in new project**.
5. Salin API key Anda (panjang sekitar 39 karakter).
> *Catatan:* Gemini Flash free tier memberikan 15 permintaan per menit (RPM) dan 1.500 permintaan per hari—lebih dari cukup untuk bot ini!

---

### Langkah 2: Buat Bot Telegram & Dapatkan Chat ID
1. **Buat Bot via @BotFather**:
   - Buka aplikasi Telegram, cari `@BotFather` (pastikan ada centang biru).
   - Kirim pesan `/newbot`.
   - Beri nama bot (contoh: `Job Hunter Alert`).
   - Beri username bot berakhiran `bot` (contoh: `my_mobile_job_alert_bot`).
   - BotFather akan memberikan **HTTP API Token** (format: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Simpan sebagai `TELEGRAM_BOT_TOKEN`.
2. **Kirim Pesan Pertama ke Bot**:
   - Buka bot yang baru Anda buat di Telegram, klik tombol **Start** atau kirim pesan `Halo`. (Wajib dilakukan agar bot bisa mengirim pesan ke Anda).
3. **Dapatkan Chat ID Anda**:
   - Cari bot `@userinfobot` atau `@getmyid_bot` di Telegram.
   - Kirim pesan apa saja, bot tersebut akan membalas dengan `Id: 123456789`.
   - Angka ini adalah `TELEGRAM_CHAT_ID` Anda.

---

### Langkah 3: Setup Repositori di GitHub & Konfigurasi Secrets

1. **Push Proyek ke GitHub**:
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit job opportunity bot"
   git branch -M main
   git remote add origin https://github.com/<username-anda>/<nama-repo>.git
   git push -u origin main
   ```

2. **Atur GitHub Repository Secrets**:
   - Buka repository Anda di GitHub di browser.
   - Pergi ke **Settings** > **Secrets and variables** > **Actions**.
   - Klik **New repository secret**, tambahkan:
     - `GEMINI_API_KEY`: API key dari Google AI Studio.
     - `GEMINI_MODEL`: `gemini-2.5-flash` *(opsional, default ke gemini-2.5-flash)*.
     - `TELEGRAM_BOT_TOKEN`: Token bot dari @BotFather.
     - `TELEGRAM_CHAT_ID`: ID angka Telegram Anda.

3. **Pastikan Izin Workflow Aktif**:
   - Di tab **Settings** > **Actions** > **General**:
   - Pada bagian **Workflow permissions**, pilih **Read and write permissions** (agar bot bisa meng-update `seen.json` otomatis).
   - Centang **Allow GitHub Actions to create and approve pull requests**.
   - Klik **Save**.

---

### Langkah 4: Sesuaikan Profil Anda di `config/profile.md`
Buka file `config/profile.md` dan ubah isinya sesuai keahlian Anda:
- Nama & tahun pengalaman mobile dev (Flutter / Android Kotlin / React Native).
- 2-3 contoh aplikasi yang pernah Anda buat (beserta teknologi & tautan GitHub/Play Store).
- Rate harga atau ketersediaan waktu.

> *Gemini akan membaca file ini secara otomatis saat membuat draft balasan, memastikan draft DM menyebutkan proyek nyata Anda dan tidak mengada-ada!*

---

### Langkah 5: Uji Coba Lokal di Komputer Anda

1. **Install Dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Salin File Environment**:
   ```bash
   cp .env.example .env
   ```
   Lalu buka `.env` dan isi token asli Anda.

3. **Tes Koneksi Telegram**:
   ```bash
   python main.py --test-telegram
   ```
   *Jika berhasil, bot Telegram akan langsung mengirimkan pesan konfirmasi ke HP Anda!*

4. **Jalankan Mode Dry-Run (Simulasi)**:
   ```bash
   python main.py --dry-run
   ```
   *Mode ini akan memindai semua sumber data, memfilter lowongan, dan mencetak contoh evaluasi AI serta draft balasan ke terminal tanpa mengirim pesan Telegram dan tanpa memodifikasi `seen.json`.*

5. **Jalankan Unit Test**:
   ```bash
   pytest tests/
   ```

---

### Langkah 6: Jalankan Secara Otomatis di GitHub Actions

Workflow otomatis sudah siap di `.github/workflows/bot.yml`:
- **Jadwal Otomatis**: Berjalan tiap 20 menit (`cron: '*/20 * * * *'`).
- **Trigger Manual**:
  1. Masuk ke repository di GitHub.
  2. Buka tab **Actions** di menu atas.
  3. Klik workflow **Job Opportunity Bot** di sisi kiri.
  4. Klik menu dropdown **Run workflow** lalu tekan tombol hijau **Run workflow**.
- Begitu ada lowongan baru yang cocok, notifikasi akan langsung masuk ke Telegram HP Anda!

---

## ⚙️ Kustomisasi `config.yaml`

| Bagian | Pengaturan | Keterangan |
| :--- | :--- | :--- |
| `settings.max_gemini_calls_per_run` | `10` | Batas postingan yang dievaluasi per eksekusi agar hemat kuota AI |
| `settings.relevance_threshold` | `6` | Nilai minimal (1-10) untuk dikirim ke Telegram (abaikan postingan di bawah ini) |
| `settings.max_post_age_hours` | `24` | Hanya ambil postingan 24 jam terakhir |
| `keywords.include` | `flutter, kotlin, android...` | Kata kunci wajib kategori mobile |
| `keywords.hiring` | `hiring, remote, freelance...` | Kata kunci penawaran kerja |
| `keywords.exclude` | `unpaid, internship, [for hire]` | Kata kunci yang langsung ditolak |
| `sources.reddit.subreddits` | `forhire, FlutterDev...` | Daftar subreddit yang dipantau |

---

## 💡 Troubleshooting & Pertanyaan Umum

### 1. Pesan Notifikasi Tidak Masuk ke Telegram
- Pastikan Anda sudah mengklik tombol **Start** di bot Telegram Anda terlebih dahulu. Bot Telegram tidak diizinkan mengirim pesan ke akun yang belum pernah memulai chat dengannya.
- Jalankan `python main.py --test-telegram` untuk memverifikasi chat ID dan bot token.

### 2. Mengatasi Rate Limit Gemini (HTTP 429)
- Bot dilengkapi sistem **exponential backoff** otomatis (coba ulang setelah 2s, 4s, 8s).
- Jika kuota gratis harian Anda habis, bot **tidak akan mogok atau kehilangan peluang**. Bot secara otomatis beralih menggunakan **Template Statis** berkualitas tinggi yang dikonfigurasi di `config.yaml` dengan badge penanda khusus.

### 3. Cron GitHub Actions Terlambat Beberapa Menit
- Pada akun gratis GitHub Actions, jadwal cron dieksekusi dalam antrean bersama. Keterlambatan antara 3–10 menit adalah hal wajar.
- Karena bot mengecek postingan hingga 24 jam terakhir dan menduplikasi via `seen.json`, Anda **tidak akan pernah kehilangan postingan**, meskipun cron terlambat beberapa menit.

### 4. Batasan Menit GitHub Actions (Repo Public vs Private)
- **Repositori Public**: Menit GitHub Actions adalah **100% GRATIS TANPA BATAS**. Anda bisa menyetel interval 15–20 menit tanpa khawatir kehabisan kuota!
- **Repositori Private**: Akun gratis GitHub memiliki kuota 2.000 menit per bulan.
  - *Saran*: Jika menggunakan repo private, ubah cron ke `0 */2 * * *` (setiap 2 jam) atau `0 */3 * * *` (setiap 3 jam) agar kuota 2.000 menit cukup untuk sebulan penuh.

---

## 🔮 Ide Pengembangan Berikutnya (Next Level Features)
1. **Dukungan Upwork RSS**: Tambahkan URL pencarian RSS feed dari akun Upwork Anda ke daftar `sources.rss.feeds`.
2. **Kategori Web & Backend**: Tambahkan profil sekunder jika Anda juga menerima proyek Fullstack (Node.js/Next.js).
3. **Filter Budget Minimal**: Perintahkan Gemini untuk mengekstrak angka budget dan menolak proyek di bawah rate minimal Anda (misal < $500).
