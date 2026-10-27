# 🧵 Mobile Job Opportunity Bot (Meta Threads Source)

> **Bot Pemantau Peluang & Lowongan Mobile Development Otomatis via Meta Threads Resmi (Rp0)**
> Memantau postingan publik di Meta Threads menggunakan **Graph API Resmi (Tanpa Scraping)**, menyaring lowongan dengan filter kata utuh (`\b`) cerdas, lalu menggunakan **Google Gemini AI** untuk menilai relevansi dan menyusun **DRAFT Balasan (Komentar & DM)** yang siap dikirim langsung ke **Telegram** Anda.

---

## 🔒 Kebijakan Keamanan & Privasi
- **Zero Scraping:** 100% menggunakan API resmi Meta Threads (`graph.threads.net/v1.0/keyword_search`). Dilarang keras menggunakan headless browser, akun bot palsu, atau teknik scraping yang melanggar Terms of Service.
- **Zero Auto-Spam:** Bot **TIDAK PERNAH** melakukan auto-reply, auto-post, atau auto-DM. Bot hanya membaca dan mengirim notifikasi beserta draft ke Telegram pribadi Anda. Anda yang mereview dan mengirimkannya sendiri secara manual.
- **Perlindungan Rahasia:** Tidak ada API key, token, atau secret yang disimpan di dalam kode maupun dicetak ke log. Seluruh kredensial dikelola via environment variable `.env` lokal atau GitHub Secrets.

---

## 🏗️ Struktur Proyek

```text
├── main.py                  # Entry point orchestrator pipeline Threads -> filter -> Gemini -> Telegram
├── config.yaml              # Konfigurasi keyword Threads, filter kata utuh, dan settings
├── config/
│   └── profile.md           # Profil mobile developer Anda (dibaca oleh Gemini)
├── prompts/
│   └── draft.txt            # System prompt instruksi Gemini untuk evaluasi & pembuatan draft balasan
├── sources/                 # Modul sumber data Meta Threads
│   ├── __init__.py
│   ├── base.py              # Definisi JobItem dataclass dan BaseSource interface
│   └── threads.py           # Pemanggil resmi Meta Threads Keyword Search API
├── core/                    # Logika inti sistem
│   ├── __init__.py
│   ├── filters.py           # Filter kata utuh (regex \b), pencegah eksposur palsu & pencari kerja
│   ├── gemini_client.py     # Gemini client (flash-lite), timeout 45s, jeda 6s, no-fake-score fallback
│   ├── notifier.py          # Pengirim Telegram format HTML (single-tap copyable <code>, tombol Threads)
│   ├── storage.py           # Persistence state seen.json (dibatasi 5000 ID) & rate-limit peringatan
│   └── threads_token.py     # Pengelola inspeksi, refresh token jangka panjang (th_refresh_token), & exchange
├── scripts/
│   └── refresh_token.py     # Skrip manual pembaruan token 60 hari tanpa menyimpan secret ke repo
├── tests/                   # Unit test otomatis (pytest)
│   ├── __init__.py
│   ├── test_threads.py      # Uji mock API Threads, penanganan HTTP 401, 403, dan token manager
│   ├── test_filters.py      # Uji regex kata utuh (\b), expo vs exposure, penolakan pencari kerja
│   └── test_gemini.py       # Uji parsing JSON, limit 429 beruntun, dan validasi profile.md
├── seen.json                # Database penampung ID Threads yang sudah diproses
├── requirements.txt         # Dependensi Python minimal (requests, feedparser, python-dotenv, pyyaml, pytest)
├── .env.example             # Contoh template environment variables (hanya placeholder)
├── .gitignore               # Konfigurasi pengabaian file rahasia (.env) dan cache
├── .github/workflows/
│   └── bot.yml              # GitHub Actions cron setiap 30 menit (GRATIS) + auto-commit seen.json
└── README.md                # Dokumentasi lengkap panduan setup
```

---

## 🚀 Panduan Setup Lengkap dari Nol (Langkah Demi Langkah)

### Langkah 1: Buat Meta App & Dapatkan Token Threads

1. **Daftar Meta for Developers**:
   - Buka [developers.facebook.com](https://developers.facebook.com/) dan login dengan akun Meta/Facebook Anda.
   - Klik **My Apps** > **Create App**.
   - Pilih jenis use-case: **Other** > **Business** (atau **Threads API** jika tersedia langsung).
   - Beri nama aplikasi Anda (contoh: `Job Hunter Alert`).

2. **Tambahkan Use Case Threads**:
   - Di App Dashboard, pada menu **Add products to your app**, cari **Threads** dan klik **Set up**.
   - Tambahkan permission:
     - `threads_basic` (izin dasar profil dan konten)
     - `threads_keyword_search` (izin pencarian keyword postingan publik)

3. **Tambahkan Akun sebagai Threads Tester**:
   - Di menu sisi kiri, klik **App Roles** > **Roles**.
   - Pada bagian **Threads Testers**, klik **Add Threads Testers**.
   - Masukkan username Threads Anda (contoh: `username_anda`).
   - Buka aplikasi Threads di HP Anda: buka **Settings** > **Account** > **Website permissions** > **Invites**, lalu terima undangan tester.

4. **Generate Long-Lived User Access Token**:
   - Kembali ke Meta Developers Dashboard > **Threads** > **User Token Generator**.
   - Klik **Generate Token** di samping username Threads Anda.
   - Berikan izin saat jendela otorisasi muncul.
   - Salin token berumur panjang (~60 hari) yang dihasilkan.
   > **PENTING**: Token ini bersifat rahasia. Jangan pernah membagikannya atau meng-commit-nya ke git!

---

### Langkah 2: Dapatkan Gemini API Key Gratis

1. Kunjungi [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Login dengan akun Google Anda dan klik **Get API key** > **Create API key**.
3. Salin API key Anda. Model default yang digunakan adalah `gemini-3.1-flash-lite` yang sangat cepat, hemat kuota, dan gratis.

---

### Langkah 3: Buat Bot Telegram & Ambil Chat ID

1. **Buat Bot via @BotFather**:
   - Buka Telegram, cari `@BotFather`, lalu kirim `/newbot`.
   - Ikuti instruksi dan salin **HTTP API Token** (format: `123456789:ABCdefGhIJK...`).
2. **Aktifkan Chat**:
   - Buka bot yang baru dibuat di Telegram dan tekan tombol **Start** (wajib dilakukan pertama kali).
3. **Cari Chat ID Anda**:
   - Kirim pesan ke `@userinfobot` di Telegram. Bot akan membalas dengan ID angka Anda (contoh: `123456789`).

---

### Langkah 4: Konfigurasi File `.env` & `config/profile.md`

1. **Salin file template environment**:
   ```bash
   cp .env.example .env
   ```
2. **Edit `.env`** dan masukkan kredensial Anda:
   ```env
   THREADS_ACCESS_TOKEN=THQW...token_anda_dari_user_token_generator
   THREADS_APP_ID=
   THREADS_APP_SECRET=
   GEMINI_API_KEY=AIzaSy...api_key_gemini_anda
   GEMINI_MODEL=gemini-3.1-flash-lite
   TELEGRAM_BOT_TOKEN=123456789:ABC...
   TELEGRAM_CHAT_ID=123456789
   ```
   *(Catatan: `THREADS_APP_ID` dan `THREADS_APP_SECRET` opsional jika Anda sudah memakai token dari User Token Generator).*

3. **Isi `config/profile.md`**:
   Buka file `config/profile.md` dan gantikan seluruh placeholder (seperti nama, keahlian Flutter/Kotlin/React Native, link GitHub/portofolio asli Anda).
   > *Jika placeholder seperti `yourusername` belum diganti, bot akan menolak mengirim notifikasi demi mencegah pengiriman draft dengan data palsu.*

---

### Langkah 5: Pengujian Lokal di Komputer Anda

1. **Install Dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Uji Koneksi Telegram**:
   ```bash
   python main.py --test-telegram
   ```
   *Pesan verifikasi akan langsung masuk ke HP Anda.*

3. **Uji Koneksi Threads API**:
   ```bash
   python main.py --test-threads
   ```
   *Bot akan memanggil API Threads dan menampilkan jumlah postingan serta 3 contoh hasil tanpa menyentuh Gemini atau Telegram.*

4. **Jalankan Simulasi Penuh (Dry Run)**:
   ```bash
   python main.py --dry-run
   ```
   *Seluruh alur dijalankan (Threads -> regex filter -> evaluasi Gemini), dan hasil dicetak ke terminal tanpa mengirim pesan Telegram dan tanpa memodifikasi `seen.json`.*

5. **Jalankan Unit Test**:
   ```bash
   pytest tests/ -v
   ```

---

### Langkah 6: Setup GitHub Actions (Otomatis & Gratis)

1. **Push ke GitHub**:
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit threads job opportunity bot"
   git branch -M main
   git remote add origin https://github.com/<username>/<repo>.git
   git push -u origin main
   ```

2. **Isi GitHub Secrets**:
   Buka repositori Anda di GitHub > **Settings** > **Secrets and variables** > **Actions** > **New repository secret**. Tambahkan:
   - `THREADS_ACCESS_TOKEN`
   - `THREADS_APP_ID` (opsional)
   - `THREADS_APP_SECRET` (opsional)
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL` (default: `gemini-3.1-flash-lite`)
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

3. **Atur Izin Workflow**:
   Di tab **Settings** > **Actions** > **General** > **Workflow permissions**, pilih **Read and write permissions** (agar bot dapat melakukan auto-commit pada `seen.json`).

4. Bot akan otomatis berjalan **setiap 30 menit** melalui cron GitHub Actions gratis! Anda juga bisa menjalankannya secara manual kapan saja melalui tombol **Run workflow** di tab Actions.

---

## 🔄 Cara Memperpanjang Token Threads (Setiap ~60 Hari)

Token dari User Token Generator Meta bertahan selama 60 hari dan dapat diperpanjang secara resmi melalui endpoint `th_refresh_token`:

1. Jalankan skrip pembaruan token:
   ```bash
   python scripts/refresh_token.py
   ```
2. Skrip akan mencetak token baru yang sudah diperpanjang beserta tanggal kedaluwarsanya.
3. Salin token baru tersebut ke `.env` lokal dan ke GitHub Secret `THREADS_ACCESS_TOKEN` Anda.
4. Jika sisa masa berlaku token Anda kurang dari 10 hari, bot secara otomatis akan mengirimkan notifikasi pengingat ke Telegram Anda.

---

## 💡 Troubleshooting & Penanganan Kendala

### 1. HTTP 403 Forbidden pada Threads API
- **Penyebab**: Aplikasi Meta Anda belum memiliki izin `threads_keyword_search` aktif.
- **Kondisi Sebelum App Review Disetujui**: Sebelum aplikasi Anda lolos App Review Meta, API hanya akan mengembalikan postingan yang dibuat oleh akun tester Anda sendiri. Untuk mengujinya, buat postingan uji coba di akun Threads Anda yang mengandung kata `flutter developer hiring` lalu jalankan `python main.py --test-threads`.
- **Solusi Produksi**: Ajukan App Review untuk permission `threads_keyword_search` di Meta Developer Dashboard.

### 2. HTTP 401 Unauthorized / Token Expired
- **Penyebab**: Token Threads sudah melewati 60 hari atau telah di-revoke.
- **Solusi**: Buka kembali User Token Generator di App Dashboard Meta dan klik *Generate Token* baru, lalu perbarui `.env` dan GitHub Secrets Anda.

### 3. HTTP 429 Rate Limit (Gemini atau Threads)
- **Threads API**: Memiliki batas 2.200 kueri per 24 jam. Bot sudah dikonfigurasi dengan jeda 1,5 detik antar kueri dan maksimal 10 request per eksekusi.
- **Gemini API**: Bot memiliki exponential backoff otomatis dan menghormati header `Retry-After`. Jika terjadi 2 kali error 429 berturut-turut, bot akan menghentikan pemanggilan AI untuk sisa run tersebut dan mengirimkan 1 peringatan ke Telegram. Postingan yang lolos filter tetap dikirim dengan label *"⚠️ Tanpa penilaian AI"* dan **tidak dimasukkan ke `seen.json`**, sehingga akan dievaluasi ulang saat kuota Gemini pulih.

### 4. "Isi config/profile.md dulu"
- Bot mendeteksi masih ada teks placeholder contoh (seperti `yourusername` atau `[Nama Lengkap Anda]`). Buka file `config/profile.md` dan lengkapi dengan data asli Anda.
