#!/usr/bin/env python3
"""Manual utility script to refresh Meta Threads Long-Lived User Access Token.

Usage:
    python scripts/refresh_token.py

Catatan Keamanan:
    Skrip ini TIDAK menyimpan token baru ke file repo secara otomatis.
    Anda harus menyalin token yang tercetak dan memperbarui file .env lokal
    serta GitHub Secrets repositori Anda secara mandiri.
"""
from __future__ import annotations

import os
import sys
from dotenv import load_dotenv

# Ensure applet root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.threads_token import ThreadsTokenManager
from sources.threads import mask_secret

load_dotenv()


def main() -> None:
    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()

    if not token or token.startswith("ISI_"):
        print("❌ ERROR: THREADS_ACCESS_TOKEN belum diatur atau masih berisi placeholder di .env.")
        print("Silakan isi token dari User Token Generator Meta terlebih dahulu.")
        sys.exit(1)

    print(f"🔄 Memulai refresh token Threads untuk token saat ini: {mask_secret(token)}")
    mgr = ThreadsTokenManager(access_token=token)
    success, new_token, expires_in, expiry_info = mgr.refresh_long_lived_token()

    if success and new_token:
        print("\n" + "=" * 65)
        print("✅ TOKEN THREADS BERHASIL DIPERBARUI!")
        print(f"Masa Berlaku Baru: Hingga {expiry_info} (~{expires_in // 86400} hari)")
        print(f"Masked Token: {mask_secret(new_token)}")
        print("=" * 65)
        print("\n📋 PETUNJUK TINDAK LANJUT (PENTING):")
        print("1. Salin token baru di bawah ini ke file .env Anda (THREADS_ACCESS_TOKEN):")
        print(f"\n{new_token}\n")
        print("2. Buka GitHub > Settings > Secrets and variables > Actions.")
        print("3. Perbarui secret 'THREADS_ACCESS_TOKEN' dengan token baru ini.")
        print("4. Amankan token ini dan jangan pernah commit token ke repository publik!\n")
    else:
        print("\n" + "=" * 65)
        print(f"❌ GAGAL MEMPERBARUI TOKEN: {expiry_info}")
        print("Catatan: Token Threads berumur panjang hanya bisa diperbarui setelah berumur minimal 24 jam.")
        print("Jika token sudah kedaluwarsa penuh (60 hari), buat token baru di User Token Generator.")
        print("=" * 65 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
