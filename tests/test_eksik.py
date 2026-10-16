import copy
import json
from datetime import date
from pathlib import Path

import pytest

from eksik import kontrol_et

ORNEK = json.loads((Path(__file__).parents[1] / "skills/cv-hazirla/examples/ornek-profil.json").read_text(encoding="utf-8"))
BUGUN = date(2026, 10, 16)


def bul(bulgular, alan, seviye=None):
    return [b for b in bulgular if b["alan"] == alan and (seviye is None or b["seviye"] == seviye)]


@pytest.fixture
def profil():
    return copy.deepcopy(ORNEK)


def test_ornek_profil_eksiksiz(profil):
    engel = [b for b in kontrol_et(profil, BUGUN) if b["seviye"] in ("zorunlu", "hata")]
    assert engel == []


def test_bos_profil_cokmez_ve_zorunlulari_sorar():
    bulgular = kontrol_et({}, BUGUN)
    alanlar = {b["alan"] for b in bulgular if b["seviye"] == "zorunlu"}
    assert {"kisisel.ad_soyad", "kisisel.eposta", "kisisel.telefon", "ozet", "egitim", "yetkinlikler"} <= alanlar


def test_staj_tarihi_yoksa_kurum_adiyla_sorar(profil):
    d = profil["deneyim"][0]
    d["baslangic"] = ""
    d["bitis"] = None
    b = bul(kontrol_et(profil, BUGUN), "deneyim[0].baslangic", "zorunlu")
    assert len(b) == 1
    assert "Örnek Teknoloji" in b[0]["soru"] and "bitiş" in b[0]["soru"]


def test_yalniz_bitis_eksik(profil):
    profil["deneyim"][0]["bitis"] = "  "
    assert bul(kontrol_et(profil, BUGUN), "deneyim[0].bitis", "zorunlu")


def test_devam_bitis_kabul(profil):
    profil["deneyim"][0]["bitis"] = "Devam ediyor"
    assert not bul(kontrol_et(profil, BUGUN), "deneyim[0].bitis")


def test_bitis_baslangictan_once_hata(profil):
    profil["deneyim"][0]["baslangic"] = "09/2025"
    profil["deneyim"][0]["bitis"] = "07/2025"
    assert bul(kontrol_et(profil, BUGUN), "deneyim[0].bitis", "hata")


@pytest.mark.parametrize("deger", ["Temmuz 2025", "7/2025", "13/2025", "2025-07", "07/25", "", 2025])
def test_gecersiz_tarih_bicimi(profil, deger):
    profil["deneyim"][0]["baslangic"] = deger
    bulgular = bul(kontrol_et(profil, BUGUN), "deneyim[0].baslangic")
    assert bulgular and bulgular[0]["seviye"] in ("hata", "zorunlu")


def test_yalniz_yil_oneri(profil):
    profil["deneyim"][0]["baslangic"] = "2025"
    profil["deneyim"][0]["bitis"] = "2025"
    bulgular = bul(kontrol_et(profil, BUGUN), "deneyim[0].baslangic")
    assert [b["seviye"] for b in bulgular] == ["oneri"]


def test_gelecekte_baslangic_hata(profil):
    profil["deneyim"][0]["baslangic"] = "01/2030"
    profil["deneyim"][0]["bitis"] = "devam"
    assert bul(kontrol_et(profil, BUGUN), "deneyim[0].baslangic", "hata")


def test_egitimde_gelecek_mezuniyet_serbest(profil):
    profil["egitim"][0]["bitis"] = "06/2028"
    assert not bul(kontrol_et(profil, BUGUN), "egitim[0].bitis")


def test_bosluklu_maddeler_bos_sayilir(profil):
    profil["deneyim"][0]["maddeler"] = ["", "   "]
    assert bul(kontrol_et(profil, BUGUN), "deneyim[0].maddeler", "zorunlu")


def test_olculebilir_sonuc_yoksa_oneri(profil):
    profil["deneyim"][0]["maddeler"] = ["Backend servisleri geliştirdim."]
    assert bul(kontrol_et(profil, BUGUN), "deneyim[0].maddeler", "oneri")


def test_emoji_hata(profil):
    profil["ozet"] = profil["ozet"] + " 🚀"
    assert bul(kontrol_et(profil, BUGUN), "ozet", "hata")


@pytest.mark.parametrize("eposta", ["ayse", "ayse@", "ayse@example", "a b@example.com"])
def test_gecersiz_eposta(profil, eposta):
    profil["kisisel"]["eposta"] = eposta
    assert bul(kontrol_et(profil, BUGUN), "kisisel.eposta", "hata")


def test_gecersiz_telefon(profil):
    profil["kisisel"]["telefon"] = "12ab"
    assert bul(kontrol_et(profil, BUGUN), "kisisel.telefon", "hata")


def test_sertifika_tarihi_yoksa_zorunlu(profil):
    profil["sertifikalar"][0]["tarih"] = ""
    assert bul(kontrol_et(profil, BUGUN), "sertifikalar[0].tarih", "zorunlu")


def test_deneyim_yoksa_yalniz_oneri(profil):
    profil["deneyim"] = []
    bulgular = bul(kontrol_et(profil, BUGUN), "deneyim")
    assert [b["seviye"] for b in bulgular] == ["oneri"]


def test_yetkinlik_gruplari_bossa_zorunlu(profil):
    profil["yetkinlikler"] = [{"kategori": "Diller", "ogeler": []}]
    assert bul(kontrol_et(profil, BUGUN), "yetkinlikler", "zorunlu")
