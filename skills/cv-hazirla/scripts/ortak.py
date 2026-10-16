"""Scriptlerin ortak yardımcıları: profil okuma ve tarih ayrıştırma."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

DEVAM_KELIMELERI = {"devam", "devam ediyor", "halen", "günümüz", "present", "current", "ongoing"}

_AY_YIL = re.compile(r"^(0[1-9]|1[0-2])/(\d{4})$")
_YIL = re.compile(r"^(\d{4})$")


class TarihHatasi(ValueError):
    pass


def profil_oku(yol: str | Path) -> dict:
    with open(yol, encoding="utf-8") as f:
        veri = json.load(f)
    if not isinstance(veri, dict):
        raise ValueError("profil.json bir JSON nesnesi olmalı")
    return veri


def bos_mu(deger) -> bool:
    """None, boş metin, yalnız boşluk ve boş liste boş sayılır."""
    if deger is None:
        return True
    if isinstance(deger, str):
        return deger.strip() == ""
    if isinstance(deger, (list, dict)):
        return len(deger) == 0
    return False


def devam_mi(deger) -> bool:
    return isinstance(deger, str) and deger.strip().lower() in DEVAM_KELIMELERI


def tarih_coz(deger: str) -> tuple[int, int | None]:
    """'AA/YYYY' -> (yıl, ay), 'YYYY' -> (yıl, None). Başka biçimde TarihHatasi."""
    if not isinstance(deger, str):
        raise TarihHatasi(f"tarih metin olmalı: {deger!r}")
    s = deger.strip()
    m = _AY_YIL.match(s)
    if m:
        return int(m.group(2)), int(m.group(1))
    m = _YIL.match(s)
    if m:
        return int(m.group(1)), None
    raise TarihHatasi(f"tarih AA/YYYY biçiminde olmalı: {deger!r}")


def tarih_sirasi(deger: str) -> tuple[int, int]:
    """Karşılaştırma anahtarı. Ay bilinmiyorsa yıl başı sayılır."""
    yil, ay = tarih_coz(deger)
    return yil, ay or 1


def bugun_anahtari(bugun: date | None = None) -> tuple[int, int]:
    b = bugun or date.today()
    return b.year, b.month
