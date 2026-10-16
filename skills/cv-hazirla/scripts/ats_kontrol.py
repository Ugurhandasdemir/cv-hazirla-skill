#!/usr/bin/env python3
"""Derlenmiş CV PDF'ini bir ATS gibi düz metne çevirip okunabilirliğini denetler.

Kullanım:
    python3 ats_kontrol.py cv.pdf --profil profil.json
    python3 ats_kontrol.py cv.pdf --profil profil.json --anahtar "Python,Docker,REST API"
    python3 ats_kontrol.py cv.pdf --anahtar-dosyasi anahtarlar.txt --max-sayfa 1

Denetimler:
    - PDF'ten metin çıkıyor mu (görsel/taranmış CV ATS'de boş görünür)
    - ad, e-posta, telefon çıkan metinde birebir var mı
    - Türkçe karakterler bozulmadan çıkıyor mu (ad soyadı üzerinden)
    - fi/fl gibi bitişik harf (ligatür) ve özel kullanım alanı karakteri var mı
    - standart bölüm başlıkları bulunuyor mu
    - sayfa sayısı sınırı
    - ilan anahtar kelimelerinin kaçı metinde geçiyor

Gerekenler: poppler-utils (pdftotext, pdfinfo).
Çıkış kodu: hata varsa 1, yalnız uyarı varsa 0.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import unicodedata

from ortak import bos_mu, profil_oku

LIGATURLER = re.compile("[ﬀ-ﬆ]")
OZEL_KULLANIM = re.compile("[-]")
BASLIK_TR = ["Deneyim", "Eğitim", "Yetkinlik"]
BASLIK_EN = ["Experience", "Education", "Skills"]


def pdf_metni(yol: str) -> str:
    return subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", yol, "-"],
                          check=True, capture_output=True, text=True).stdout


def sayfa_sayisi(yol: str) -> int:
    cikti = subprocess.run(["pdfinfo", yol], check=True, capture_output=True, text=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", cikti, re.M)
    return int(m.group(1)) if m else 0


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"\s+", " ", s).casefold()


_TR_ASCII = str.maketrans("ıİğĞüÜşŞöÖçÇ", "iIgGuUsSoOcC")


def _iskelet(s: str) -> str:
    """Türkçe ve aksanlı harfleri ASCII'ye indirir, harf dışını atar: bozulmuş çıkarımı yakalamak için."""
    s = unicodedata.normalize("NFKD", s.translate(_TR_ASCII)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


def _rakamlar(s: str) -> str:
    return re.sub(r"\D", "", s)


def anahtar_var_mi(anahtar: str, metin_norm: str) -> bool:
    a = _norm(anahtar).strip()
    if not a:
        return True
    # Kelime sınırı: "Java" kelimesi "JavaScript" içinde sayılmasın, "C++" ve "C#" gibi işaretli adlar da çalışsın.
    desen = r"(?<![\w])" + re.escape(a) + r"(?![\w+#])"
    return re.search(desen, metin_norm) is not None


def denetle(metin: str, sayfa: int, profil: dict | None, anahtarlar: list[str], max_sayfa: int) -> dict:
    hatalar: list[str] = []
    uyarilar: list[str] = []
    bilgi: list[str] = []
    norm = _norm(metin)

    if len(metin.strip()) < 200:
        hatalar.append("PDF'ten neredeyse hiç metin çıkmadı. CV görsel ya da taranmış olabilir, ATS boş görür.")

    if LIGATURLER.search(metin):
        hatalar.append("Metinde bitişik harf (ﬁ/ﬂ) var. ATS 'fi' içeren kelimeleri bulamaz. Yazı tipinde ligatürü kapat.")
    if OZEL_KULLANIM.search(metin):
        hatalar.append("Metinde özel kullanım alanı karakteri var (genelde ikon fontu). ATS bunu çöp karakter okur.")

    if sayfa > max_sayfa:
        hatalar.append(f"CV {sayfa} sayfa, sınır {max_sayfa}.")

    if profil:
        dil = profil.get("dil", "tr")
        k = profil.get("kisisel") or {}
        ad = k.get("ad_soyad")
        if not bos_mu(ad):
            if _norm(ad) in norm:
                bilgi.append("Ad soyad metinde birebir var.")
            else:
                if _iskelet(ad) in _iskelet(metin):
                    hatalar.append(f"Ad '{ad}' metinde Türkçe karakterleri bozulmuş olarak çıkıyor.")
                else:
                    hatalar.append(f"Ad '{ad}' çıkan metinde bulunamadı.")
        eposta = k.get("eposta")
        if not bos_mu(eposta) and _norm(eposta) not in norm:
            hatalar.append(f"E-posta '{eposta}' çıkan metinde yok ya da bölünmüş.")
        tel = k.get("telefon")
        if not bos_mu(tel) and _rakamlar(tel) not in _rakamlar(metin):
            uyarilar.append(f"Telefon '{tel}' çıkan metinde birebir bulunamadı.")
        basliklar = BASLIK_EN if dil == "en" else BASLIK_TR
    else:
        basliklar = BASLIK_TR if "eğitim" in norm else BASLIK_EN

    for b in basliklar:
        if _norm(b) not in norm:
            uyarilar.append(f"Standart başlık '{b}' bulunamadı. ATS bölümleri başlıktan tanır.")

    bulunan, eksik = [], []
    for a in anahtarlar:
        (bulunan if anahtar_var_mi(a, norm) else eksik).append(a.strip())
    if anahtarlar:
        oran = len(bulunan) / len(anahtarlar)
        bilgi.append(f"İlan anahtar kelimeleri: {len(bulunan)}/{len(anahtarlar)} (%{oran * 100:.0f}).")
        if eksik:
            uyarilar.append("Metinde geçmeyen anahtar kelimeler: " + ", ".join(eksik)
                            + ". Adayda gerçekten varsa ilgili madde ya da yetkinlik satırına eklenebilir, yoksa eklenmez.")

    return {"hatalar": hatalar, "uyarilar": uyarilar, "bilgi": bilgi, "sayfa": sayfa,
            "bulunan": bulunan, "eksik": eksik}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--profil")
    ap.add_argument("--anahtar", default="", help="virgülle ayrılmış ilan anahtar kelimeleri")
    ap.add_argument("--anahtar-dosyasi", help="her satırda bir anahtar kelime")
    ap.add_argument("--max-sayfa", type=int, default=2)
    args = ap.parse_args()

    for arac in ("pdftotext", "pdfinfo"):
        if not shutil.which(arac):
            print(f"{arac} bulunamadı. poppler-utils kurun (apt install poppler-utils / brew install poppler).", file=sys.stderr)
            return 2

    anahtarlar = [a for a in args.anahtar.split(",") if a.strip()]
    if args.anahtar_dosyasi:
        with open(args.anahtar_dosyasi, encoding="utf-8") as f:
            anahtarlar += [s.strip() for s in f if s.strip()]

    try:
        profil = profil_oku(args.profil) if args.profil else None
        metin = pdf_metni(args.pdf)
        sayfa = sayfa_sayisi(args.pdf)
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        print(f"okunamadı: {e}", file=sys.stderr)
        return 2

    sonuc = denetle(metin, sayfa, profil, anahtarlar, args.max_sayfa)
    print(f"Sayfa: {sonuc['sayfa']}")
    for s in sonuc["bilgi"]:
        print(f"[bilgi] {s}")
    for s in sonuc["uyarilar"]:
        print(f"[uyarı] {s}")
    for s in sonuc["hatalar"]:
        print(f"[HATA]  {s}")
    if not sonuc["hatalar"]:
        print("ATS denetimi geçti.")
    return 1 if sonuc["hatalar"] else 0


if __name__ == "__main__":
    sys.exit(main())
