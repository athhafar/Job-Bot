cat > config/profile.md << 'EOF'

# Profil Developer

> File ini dibaca otomatis oleh bot dan di-inject ke prompt Gemini AI
> untuk menyusun draft komentar dan DM.

---

## 1. Identitas

- **Nama**: Athallah Farel Hidayat
- **Role Utama**: Full-stack Developer (.NET/C# backend, Flutter mobile, IoT integration)
- **Lokasi**: Indonesia (remote, UTC+7)
- **Ketersediaan**: Freelance / Contract (remote)

---

## 2. Kemampuan Teknis

- **Backend**: C#/.NET Web API, REST API, MongoDB, Azure Functions
- **Mobile**: Flutter & Dart
- **IoT**: integrasi perangkat IoT dengan backend dan aplikasi mobile
- **Integrasi**: Firebase (Cloud Messaging), LINE Bot, API layer untuk B2B

---

## 3. Tautan Publik

- **Portofolio**: https://my-porto-gilt.vercel.app
- **GitHub**: https://github.com/athhafar
- **LinkedIn**: https://www.linkedin.com/in/athallahfarelhidayat/
- **Email Kontak**: athallahfarel6@gmail.com
  EOF

grep -nE "athhafar|TODO|\[Nama|example\.com|yourportfolio" config/profile.md
python main.py --dry-run
