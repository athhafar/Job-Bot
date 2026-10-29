# 🧵 Mobile Job Opportunity Bot (Threads Scraper Source)

> **Bot Pemantau Peluang & Lowongan Mobile Development Otomatis via Scraper Threads (Rp0)**
> Memantau postingan publik di Meta Threads menggunakan scraper **Playwright headless** (`threads-parser` dari fork), menyaring lowongan dengan filter kata utuh (`\b`) cerdas, lalu menggunakan **Google Gemini AI** untuk menilai relevansi dan menyusun **DRAFT Balasan (Komentar & DM)** yang siap dikirim langsung ke **Telegram** Anda.

---

## 🔒 Kebijakan Keamanan & Privasi
- **Zero Auto-Spam:** Bot **TIDAK PERNAH** melakukan auto-reply, auto-post, atau auto-DM. Bot hanya membaca secara anonim (tanpa login) dan mengirim notifikasi beserta draft ke Telegram pribadi Anda. Anda yang mereview dan mengirimkannya sendiri secara manual.
- **Perlindungan Rahasia:** Tidak ada API key atau secret yang disimpan di dalam kode maupun dicetak ke log. Seluruh kredensial dikelola via environment variable `.env` lokal atau GitHub Secrets.
- **Repo Private:** Repositori Job-Bot bersifat Private karena memuat data profil personal developer (`config/profile.md`).

---

## 🏗️ Struktur Proyek

```text
├── main.py                  # Entry point orchestrator pipeline Threads -> filter -> Gemini -> Telegram
├── config.yaml              # Konfigurasi keyword Threads, filter kata utuh, dan settings
├── config/
│   └── profile.md           # Profil mobile developer Anda (dibaca oleh Gemini)
├── prompts/
│   └── draft.txt            # System prompt instruksi Gemini untuk evaluasi & pembuatan draft balasan
├── sources/                 # Modul sumber data
│   ├── __init__.py
│   ├── base.py              # Definisi JobItem dataclass dan BaseSource interface
│   └── threads_scraper.py   # Pemanggil scraper Threads Playwright via subprocess terisolasi
├── core/                    # Logika inti sistem
│   ├── __init__.py
│   ├── filters.py           # Filter kata utuh (regex \b), pencegah eksposur palsu & pencari kerja
│   ├── gemini_client.py     # Gemini client (flash-lite), timeout 45s, jeda 6s, no-fake-score fallback
│   ├── notifier.py          # Pengirim Telegram format HTML (single-tap copyable <code>, tombol Threads)
│   └── storage.py           # Persistence state seen.json (dibatasi 5000 ID) & cooldown alert
├── tests/                   # Unit test otomatis (pytest)
│   ├── __init__.py
│   ├── test_threads_scraper.py # Uji parser output scraper, CLI error handling, dan jeda antar-keyword
│   ├── test_filters.py      # Uji regex kata utuh (\b), expo vs exposure, penolakan pencari kerja
│   └── test_gemini.py       # Uji parsing JSON, limit 429 beruntun, dan validasi profile.md
├── seen.json                # Database penampung ID Threads yang sudah diproses
├── requirements.txt         # Dependensi Python (threads-parser fork, playwright, gemini, dll.)
├── .env.example             # Contoh template environment variables
├── .gitignore               # Konfigurasi pengabaian file rahasia (.env) dan cache
├── .github/workflows/
│   └── bot.yml              # GitHub Actions cron setiap 60 menit (hemat kuota) + auto-commit seen.json
└── README.md                # Dokumentasi lengkap panduan setup
```

---

## 🚀 Panduan Setup Lengkap dari Nol

### Langkah 1: Dapatkan Gemini API Key Gratis

1. Kunjungi [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Login dengan akun Google Anda dan klik **Get API key** > **Create API key**.
3. Salin API key Anda. Model default yang digunakan adalah `gemini-3.1-flash-lite` yang sangat cepat, hemat kuota, dan gratis.

---

### Langkah 2: Buat Bot Telegram & Ambil Chat ID

1. **Buat Bot via @BotFather**:
   - Buka Telegram, cari `@BotFather`, lalu kirim `/newbot`.
   - Ikuti instruksi dan salin **HTTP API Token** (format: `123456789:ABCdefGhIJK...`).
2. **Aktifkan Chat**:
   - Buka bot yang baru dibuat di Telegram dan tekan tombol **Start** (wajib dilakukan pertama kali).
3. **Cari Chat ID Anda**:
   - Kirim pesan ke `@userinfobot` di Telegram. Bot akan membalas dengan ID angka Anda (contoh: `123456789`).

---

### Langkah 3: Konfigurasi File `.env` & `config/profile.md`

1. **Salin file template environment**:
   ```bash
   cp .env.example .env
   ```
2. **Edit `.env`** dan masukkan kredensial Anda:
   ```env
   GEMINI_API_KEY=AIzaSy...api_key_gemini_anda
   GEMINI_MODEL=gemini-3.1-flash-lite
   TELEGRAM_BOT_TOKEN=123456789:ABC...
   TELEGRAM_CHAT_ID=123456789
   ```

3. **Isi `config/profile.md`**:
   Buka file `config/profile.md` dan lengkapi dengan portofolio, keahlian Flutter/Kotlin/React Native, serta link GitHub asli Anda.
   *(Jika placeholder seperti `yourusername` belum diganti, bot akan menolak jalan demi mencegah pengiriman draft dengan data palsu).*

---

### Langkah 4: Pengujian Lokal di Komputer Anda

Buat virtual environment Python 3.12 dengan `uv`:

```bash
uv venv --python 3.12 --managed-python
source .venv/bin/activate
uv pip install -r requirements.txt
playwright install chromium
```

1. **Uji Koneksi Telegram**:
   ```bash
   python main.py --test-telegram
   ```
   *Pesan verifikasi akan langsung masuk ke Telegram Anda.*

2. **Uji Koneksi Scraper Threads**:
   ```bash
   python main.py --test-threads
   ```
   *Scraper akan memindai satu keyword uji dan mencetak hasil postingan tanpa memanggil Gemini atau Telegram.*

3. **Jalankan Simulasi Penuh (Dry Run)**:
   ```bash
   python main.py --dry-run
   ```
   *Seluruh alur dijalankan (Scraper -> regex filter -> evaluasi Gemini), dan hasil dicetak ke terminal tanpa mengirim pesan Telegram dan tanpa memodifikasi `seen.json`.*

4. **Jalankan Seluruh Unit Test**:
   ```bash
   pytest tests/ -v
   ```

---

### Langkah 5: Setup GitHub Actions (Otomatis & Hemat Kuota)

1. **Push ke GitHub**:
   ```bash
   git add .
   git commit -m "feat: integrate threads playwright scraper"
   git push origin main
   ```

2. **Isi GitHub Secrets**:
   Buka repositori Anda di GitHub > **Settings** > **Secrets and variables** > **Actions** > **New repository secret**. Tambahkan:
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL` (default: `gemini-3.1-flash-lite`)
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

   *(Catatan: `THREADS_ACCESS_TOKEN`, `THREADS_APP_ID`, dan `THREADS_APP_SECRET` sudah tidak digunakan dan bisa dihapus dari Secrets).*

3. **Atur Izin Workflow**:
   Di tab **Settings** > **Actions** > **General** > **Workflow permissions**, pilih **Read and write permissions** (agar GitHub Actions dapat melakukan auto-commit pembaruan `seen.json`).

4. **Jadwal Eksekusi**:
   Workflow dijalankan otomatis **setiap 60 menit** (`0 * * * *`) via GitHub Actions. Dengan browser cache Playwright, konsumsi waktu adalah ~1 - 1,5 menit/run (~720 - 1.080 menit/bulan), aman di dalam kuota 2.000 menit gratis repositori private.

---

## 🔄 Cara Memperbarui Versi Scraper

Scraper `threads-parser` dipasang langsung dari fork repositori Anda yang dikunci ke commit hash:

1. Buat commit perubahan atau pull update upstream di repo fork Anda (`Threads-Scraper-Meta`).
2. Push ke GitHub: `git push origin main`.
3. Dapatkan hash commit terbaru:
   ```bash
   git -C /Users/dit-atha/Atha/Threads-Scraper-Meta rev-parse HEAD
   ```
4. Buka `requirements.txt` di Job-Bot dan perbarui baris scraper dengan commit hash baru:
   ```text
   threads-parser @ git+https://github.com/athhafar/Threads-Scraper-Meta.git@<COMMIT_HASH_BARU>
   ```
5. Install ulang dependensi lokal:
   ```bash
   uv pip install -r requirements.txt
   ```
6. Commit dan push perubahan `requirements.txt` ke repo Job-Bot.

---

## 💡 Troubleshooting & Penanganan Kendala

### 1. `Error: Threads search results payload was not found`
- **Penyebab**: Threads tidak menemukan hasil pencarian untuk keyword tersebut dalam mode publik tanpa login, atau Threads mengembalikan halaman kosong tanpa payload GraphQL.
- **Perilaku Bot**: Bot menangani error ini dengan aman (graceful fallback). Kegagalan pada satu keyword tidak akan menghentikan pemindaian keyword lainnya.
- **Solusi**: Gunakan keyword pencarian yang lebih umum di `config.yaml` (misalnya `"flutter developer"` atau `"hiring flutter"` alih-alih kalimat spesifik yang panjang).

### 2. Hasil Scraper Kosong Sepanjang Run
- Jika selama 1 run scraper menghasilkan 0 postingan atau diblokir, bot akan mengirimkan peringatan otomatis ke Telegram (dibatasi maksimal 1 kali per 6 jam) via `seen.json` rate-limiting.
- Cek apakah Threads sedang mengubah struktur DOM atau memblokir pencarian tanpa login.

### 3. Playwright Gagal Terpasang / Browser Chromium Hilang
- Jalankan ulang instalasi browser Playwright:
  ```bash
  playwright install chromium
  ```
- Di lingkungan Linux / GitHub Actions, tambahkan `--with-deps`:
  ```bash
  playwright install --with-deps chromium
  ```

---

## ⚠️ Catatan Risiko & Etika Scraping

1. **Bukan API Resmi Meta**: Scraper ini bekerja dengan mengekstrak data dari web Threads publik. Meta sewaktu-waktu dapat memperbarui antarmuka atau endpoint GraphQL internal yang dapat menyebabkan parser memerlukan update.
2. **IP Datacenter GitHub Actions**: Alamat IP mesin GitHub Actions berasal dari Microsoft Azure/datacenter yang lebih mudah terdeteksi atau dibatasi oleh sistem proteksi Threads dibandingkan IP residensial (koneksi Wi-Fi/Mac lokal Anda). Jika run di GitHub Actions sering menghasilkan 0 postingan sementara di Mac berhasil, jalankan bot secara terjadwal di komputer lokal atau VPS residensial/pribadi.
3. **Peringatan Privasi Akun**: Selalu jalankan scraper ini dalam mode **tanpa login (guest/anonymous)**. Jangan pernah memasukkan akun Threads pribadi utama Anda ke scraper ini demi menghindari risiko pembatasan atau suspensi akun oleh platform Meta.
