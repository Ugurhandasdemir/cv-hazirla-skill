#!/usr/bin/env python3
"""profil.json'daki eksik ve hatalı alanları bulur, adaya sorulacak soruları üretir.

Kullanım:
    python3 eksik.py profil.json            # okunur liste
    python3 eksik.py profil.json --json     # makine için JSON

Seviyeler:
    zorunlu  CV bu bilgi olmadan üretilmez (ör. staj tarihi, e-posta).
    hata     Bilgi var ama geçersiz (ör. bitiş başlangıçtan önce). Düzeltilmeden üretilmez.
    oneri    CV'yi güçlendirir, aday "yok" derse atlanır (ör. ölçülebilir sonuç, GANO).

Çıkış kodu: zorunlu veya hata varsa 1, yalnız öneri varsa ya da hiç bulgu yoksa 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date

from ortak import TarihHatasi, bos_mu, bugun_anahtari, devam_mi, profil_oku, tarih_coz, tarih_sirasi

EPOSTA = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TELEFON = re.compile(r"^\+?[\d\s()-]{10,20}$")
SAYI = re.compile(r"\d")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐★☆✓✔✖]")
MADDE_UZUN = 320
OZET_KISA = 150
OZET_UZUN = 700

DENEYIM_TURLERI = {"is": "iş", "staj": "staj", "gonullu": "gönüllü çalışma", "yari_zamanli": "yarı zamanlı iş"}


class Bulgular:
    def __init__(self) -> None:
        self.liste: list[dict] = []

    def ekle(self, seviye: str, alan: str, soru: str) -> None:
        self.liste.append({"seviye": seviye, "alan": alan, "soru": soru})


def _etiket(kayit: dict, varsayilan: str) -> str:
    kurum = (kayit.get("kurum") or "").strip()
    poz = (kayit.get("pozisyon") or "").strip()
    if kurum and poz:
        return f"{kurum} ({poz})"
    return kurum or poz or varsayilan


def _tarih_araligi(b: Bulgular, kayit: dict, yol: str, ad: str, bugun: tuple[int, int],
                   bitis_zorunlu: bool = True) -> None:
    bas, bit = kayit.get("baslangic"), kayit.get("bitis")
    bas_k = bit_k = None

    if bos_mu(bas) and bos_mu(bit):
        b.ekle("zorunlu", f"{yol}.baslangic", f"{ad}: başlangıç ve bitiş tarihi nedir? (AA/YYYY, sürüyorsa bitiş için 'devam')")
        return
    if bos_mu(bas):
        b.ekle("zorunlu", f"{yol}.baslangic", f"{ad}: başlangıç tarihi nedir? (AA/YYYY)")
    else:
        try:
            yil, ay = tarih_coz(bas)
            bas_k = tarih_sirasi(bas)
            if ay is None:
                b.ekle("oneri", f"{yol}.baslangic", f"{ad}: başlangıçta yalnız yıl var ({bas}). Ayını hatırlıyor musun? ATS'ler AA/YYYY'yi daha iyi okur.")
            if bas_k > bugun:
                b.ekle("hata", f"{yol}.baslangic", f"{ad}: başlangıç tarihi ({bas}) gelecekte görünüyor. Doğru mu?")
        except TarihHatasi:
            b.ekle("hata", f"{yol}.baslangic", f"{ad}: başlangıç tarihi '{bas}' okunamadı. AA/YYYY biçiminde yazar mısın?")

    if bos_mu(bit):
        if bitis_zorunlu:
            b.ekle("zorunlu", f"{yol}.bitis", f"{ad}: bitiş tarihi nedir? Hâlâ sürüyorsa 'devam' yaz.")
    elif not devam_mi(bit):
        try:
            yil, ay = tarih_coz(bit)
            bit_k = tarih_sirasi(bit)
            if ay is None:
                b.ekle("oneri", f"{yol}.bitis", f"{ad}: bitişte yalnız yıl var ({bit}). Ayını hatırlıyor musun?")
        except TarihHatasi:
            b.ekle("hata", f"{yol}.bitis", f"{ad}: bitiş tarihi '{bit}' okunamadı. AA/YYYY ya da 'devam' yazar mısın?")

    if bas_k and bit_k and bit_k < bas_k:
        b.ekle("hata", f"{yol}.bitis", f"{ad}: bitiş ({bit}) başlangıçtan ({bas}) önce. Hangisi yanlış?")


def _maddeler(b: Bulgular, maddeler, yol: str, ad: str, zorunlu_soru: str) -> None:
    if bos_mu(maddeler) or not isinstance(maddeler, list) or all(bos_mu(m) for m in maddeler):
        b.ekle("zorunlu", f"{yol}.maddeler", f"{ad}: {zorunlu_soru}")
        return
    olculebilir = False
    for i, m in enumerate(maddeler):
        if not isinstance(m, str) or bos_mu(m):
            continue
        if SAYI.search(m):
            olculebilir = True
        if len(m) > MADDE_UZUN:
            b.ekle("oneri", f"{yol}.maddeler[{i}]", f"{ad}: {i + 1}. madde {len(m)} karakter. İki maddeye bölelim mi ya da kısaltalım mı?")
        if EMOJI.search(m):
            b.ekle("hata", f"{yol}.maddeler[{i}]", f"{ad}: {i + 1}. maddede emoji/simge var. ATS bunları bozuk okur, çıkaralım mı?")
    if not olculebilir:
        b.ekle("oneri", f"{yol}.maddeler", f"{ad}: ölçülebilir bir sonuç var mı? (ör. süre %X kısaldı, N kullanıcı, N rapor, doğruluk %Y). Yoksa 'yok' de, uydurmayız.")


def kontrol_et(profil: dict, bugun: date | None = None) -> list[dict]:
    b = Bulgular()
    bk = bugun_anahtari(bugun)

    # Kişisel bilgiler
    k = profil.get("kisisel") or {}
    for alan, soru in [
        ("ad_soyad", "Adın ve soyadın CV'de nasıl yazılsın?"),
        ("unvan", "CV başlığında hangi unvan yazsın? (ör. 'Yazılım Mühendisi', 'Veri Bilimi Stajyeri adayı')"),
        ("eposta", "İletişim e-posta adresin nedir?"),
        ("telefon", "Telefon numaran nedir? (+90 ile)"),
        ("sehir", "Hangi şehirde yaşıyorsun ya da çalışmak istiyorsun?"),
    ]:
        if bos_mu(k.get(alan)):
            b.ekle("zorunlu", f"kisisel.{alan}", soru)
    if not bos_mu(k.get("eposta")) and not EPOSTA.match(k["eposta"].strip()):
        b.ekle("hata", "kisisel.eposta", f"E-posta '{k['eposta']}' geçerli görünmüyor. Doğrusu nedir?")
    if not bos_mu(k.get("telefon")) and not TELEFON.match(k["telefon"].strip()):
        b.ekle("hata", "kisisel.telefon", f"Telefon '{k['telefon']}' geçerli görünmüyor. Doğrusu nedir?")
    if bos_mu(k.get("linkedin")):
        b.ekle("oneri", "kisisel.linkedin", "LinkedIn profil adresin var mı?")
    if bos_mu(k.get("github")) and not bos_mu(profil.get("projeler")):
        b.ekle("oneri", "kisisel.github", "Projelerin için GitHub (ya da portfolyo) adresin var mı?")

    # Özet
    ozet = profil.get("ozet")
    if bos_mu(ozet):
        b.ekle("zorunlu", "ozet", "Özet için: hangi alanda çalışıyorsun ya da çalışmak istiyorsun, en güçlü 2-3 becerin ne, seni diğer adaylardan ayıran bir iş/sonuç var mı?")
    else:
        if len(ozet) < OZET_KISA:
            b.ekle("oneri", "ozet", "Özet çok kısa. Hedef pozisyonun ve en güçlü becerilerinle bir iki cümle daha ekleyebilir miyiz?")
        if len(ozet) > OZET_UZUN:
            b.ekle("oneri", "ozet", f"Özet {len(ozet)} karakter, 3-4 cümleye (yaklaşık 400-600 karakter) indirelim mi?")
        if EMOJI.search(ozet):
            b.ekle("hata", "ozet", "Özette emoji/simge var. ATS bunları bozuk okur, çıkaralım mı?")

    # Deneyim (iş, staj, gönüllü)
    deneyim = profil.get("deneyim") or []
    if not deneyim:
        b.ekle("oneri", "deneyim", "Hiç staj, yarı zamanlı iş, freelance ya da gönüllü çalışman oldu mu? Kısa süreli olsa da yazılabilir.")
    for i, d in enumerate(deneyim):
        yol = f"deneyim[{i}]"
        tur = DENEYIM_TURLERI.get(d.get("tur"), "deneyim")
        ad = _etiket(d, f"{i + 1}. {tur}")
        if bos_mu(d.get("kurum")):
            b.ekle("zorunlu", f"{yol}.kurum", f"{ad}: hangi kurumda/şirkette?")
        if bos_mu(d.get("pozisyon")):
            b.ekle("zorunlu", f"{yol}.pozisyon", f"{ad}: pozisyon adın neydi? (ör. 'Yazılım Stajyeri')")
        _tarih_araligi(b, d, yol, ad, bk)
        if bos_mu(d.get("sehir")):
            b.ekle("oneri", f"{yol}.sehir", f"{ad}: hangi şehirdeydi, ya da uzaktan mıydı?")
        _maddeler(b, d.get("maddeler"), yol, ad,
                  "orada ne yaptın? 2-3 somut iş yaz: hangi problemi çözdün, hangi aracı kullandın, sonuç ne oldu?")
        if bos_mu(d.get("teknolojiler")):
            b.ekle("oneri", f"{yol}.teknolojiler", f"{ad}: hangi teknolojileri/araçları kullandın?")

    # Eğitim
    egitim = profil.get("egitim") or []
    if not egitim:
        b.ekle("zorunlu", "egitim", "Eğitim bilgin: okul, bölüm, derece (lisans/ön lisans/yüksek lisans), başlangıç ve bitiş tarihi?")
    for i, e in enumerate(egitim):
        yol = f"egitim[{i}]"
        ad = (e.get("okul") or "").strip() or f"{i + 1}. eğitim"
        for alan, soru in [("okul", "okulun adı nedir?"), ("bolum", "bölümün nedir?"), ("derece", "derece nedir? (lisans, ön lisans, yüksek lisans)")]:
            if bos_mu(e.get(alan)):
                b.ekle("zorunlu", f"{yol}.{alan}", f"{ad}: {soru}")
        _tarih_araligi(b, e, yol, ad, bk)
        if bos_mu(e.get("gano")):
            b.ekle("oneri", f"{yol}.gano", f"{ad}: GANO'nu yazmak ister misin? (ör. 3.05/4.00) İstemezsen boş kalır.")

    # Projeler
    for i, p in enumerate(profil.get("projeler") or []):
        yol = f"projeler[{i}]"
        ad = (p.get("baslik") or "").strip() or f"{i + 1}. proje"
        if bos_mu(p.get("baslik")):
            b.ekle("zorunlu", f"{yol}.baslik", f"{i + 1}. projenin kısa başlığı nedir?")
        _maddeler(b, p.get("maddeler"), yol, ad,
                  "bu projede ne yaptın? Problem, senin katkın ve sonuç (1-3 madde)?")
        if bos_mu(p.get("link")):
            b.ekle("oneri", f"{yol}.link", f"{ad}: GitHub ya da demo linki var mı?")
        if bos_mu(p.get("teknolojiler")):
            b.ekle("oneri", f"{yol}.teknolojiler", f"{ad}: hangi teknolojileri kullandın?")

    # Yetkinlikler
    yet = profil.get("yetkinlikler") or []
    if not yet or all(bos_mu(y.get("ogeler")) for y in yet):
        b.ekle("zorunlu", "yetkinlikler", "Teknik becerilerin neler? Diller, framework'ler, araçlar, veritabanları. Sadece gerçekten kullandıklarını yaz.")

    # Başarılar ve sertifikalar
    for i, s in enumerate(profil.get("basarilar") or []):
        if bos_mu(s.get("yil")):
            b.ekle("zorunlu", f"basarilar[{i}].yil", f"{s.get('baslik') or f'{i + 1}. başarı'}: hangi yıl?")
    for i, s in enumerate(profil.get("sertifikalar") or []):
        ad = s.get("ad") or f"{i + 1}. sertifika"
        if bos_mu(s.get("kurum")):
            b.ekle("oneri", f"sertifikalar[{i}].kurum", f"{ad}: hangi kurum verdi?")
        if bos_mu(s.get("tarih")):
            b.ekle("zorunlu", f"sertifikalar[{i}].tarih", f"{ad}: ne zaman aldın? (AA/YYYY)")

    # Diller
    for i, d in enumerate(profil.get("diller") or []):
        if bos_mu(d.get("seviye")):
            b.ekle("zorunlu", f"diller[{i}].seviye", f"{d.get('dil') or 'Dil'} seviyen nedir? (ör. B2, ileri, YDS 75)")
    if not profil.get("diller"):
        b.ekle("oneri", "diller", "Yabancı dil bilgin var mı? Seviyesiyle (ör. İngilizce B2).")

    # Topluluk / gönüllülük
    for i, t in enumerate(profil.get("topluluk") or []):
        _tarih_araligi(b, t, f"topluluk[{i}]", _etiket(t, f"{i + 1}. topluluk görevi"), bk)

    return b.liste


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profil")
    ap.add_argument("--json", action="store_true", help="JSON çıktı")
    args = ap.parse_args()

    try:
        profil = profil_oku(args.profil)
    except (OSError, ValueError) as e:
        print(f"profil okunamadı: {e}", file=sys.stderr)
        return 2

    bulgular = kontrol_et(profil)
    if args.json:
        print(json.dumps(bulgular, ensure_ascii=False, indent=2))
    else:
        if not bulgular:
            print("Eksik yok. CV üretilebilir.")
        sira = {"hata": 0, "zorunlu": 1, "oneri": 2}
        for x in sorted(bulgular, key=lambda x: sira[x["seviye"]]):
            print(f"[{x['seviye']:7}] {x['alan']:32} {x['soru']}")
    return 1 if any(x["seviye"] in ("zorunlu", "hata") for x in bulgular) else 0


if __name__ == "__main__":
    sys.exit(main())
