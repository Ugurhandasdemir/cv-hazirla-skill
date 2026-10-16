import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ats_kontrol import denetle, pdf_metni, sayfa_sayisi
from render import kac, uret, url_metni

KOK = Path(__file__).parents[1] / "skills/cv-hazirla"
ORNEK = json.loads((KOK / "examples/ornek-profil.json").read_text(encoding="utf-8"))


@pytest.fixture
def profil():
    return copy.deepcopy(ORNEK)


@pytest.mark.parametrize("girdi,beklenen", [
    ("R&D", r"R\&D"),
    ("%85", r"\%85"),
    ("snake_case", r"snake\_case"),
    ("C#", r"C\#"),
    ("$5", r"\$5"),
    ("{x}", r"\{x\}"),
    ("a~b", r"a\textasciitilde{}b"),
    ("2^10", r"2\textasciicircum{}10"),
    ("C:\\yol", r"C:\textbackslash{}yol"),
    (None, ""),
    (3.5, "3.5"),
])
def test_latex_kacis(girdi, beklenen):
    assert kac(girdi) == beklenen


def test_url_metni():
    assert url_metni("https://www.linkedin.com/in/x/") == "linkedin.com/in/x"
    assert url_metni("github.com/x") == "github.com/x"


def test_bos_bolumler_yazilmaz(profil):
    profil["sertifikalar"] = []
    profil["topluluk"] = []
    tex = uret(profil)
    assert "Sertifikalar" not in tex and "Topluluk" not in tex


def test_bolum_sirasi_uygulanir(profil):
    profil["bolum_sirasi"] = ["ozet", "basarilar", "deneyim", "egitim"]
    tex = uret(profil)
    assert tex.index("Yarışmalar") < tex.index("İş Deneyimi") < tex.index("{Eğitim}")
    assert "Projeler" not in tex


def test_bilinmeyen_bolum_reddedilir(profil):
    profil["bolum_sirasi"] = ["ozet", "hobiler"]
    with pytest.raises(ValueError):
        uret(profil)


def test_ingilizce_basliklar_ve_devam(profil):
    profil["dil"] = "en"
    profil["deneyim"][0]["bitis"] = "devam"
    tex = uret(profil)
    assert r"\section{Experience}" in tex and "Present" in tex and "[english]{babel}" in tex


def test_bilinmeyen_dil_turkceye_duser(profil):
    profil["dil"] = "de"
    assert r"\section{Eğitim}" in uret(profil)


def test_ligatur_kapali(profil):
    assert "Ligatures=NoCommon" in uret(profil)


def test_render_eksik_varsa_uretmez(tmp_path, profil):
    profil["deneyim"][0]["baslangic"] = ""
    p = tmp_path / "p.json"
    p.write_text(json.dumps(profil, ensure_ascii=False), encoding="utf-8")
    cikti = tmp_path / "cv.tex"
    r = subprocess.run(["python3", str(KOK / "scripts/render.py"), str(p), "-o", str(cikti)],
                       capture_output=True, text=True)
    assert r.returncode == 1 and not cikti.exists()
    assert "deneyim[0].baslangic" in r.stderr
    r = subprocess.run(["python3", str(KOK / "scripts/render.py"), str(p), "-o", str(cikti), "--zorla"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and cikti.exists()


def test_bozuk_json(tmp_path):
    p = tmp_path / "p.json"
    p.write_text("[1, 2]", encoding="utf-8")
    r = subprocess.run(["python3", str(KOK / "scripts/eksik.py"), str(p)], capture_output=True, text=True)
    assert r.returncode == 2


# --- ATS denetimi, PDF gerektirmeyen kısım ---

def test_ats_ligatur_yakalanir():
    metin = "Deneyim Eğitim Yetkinlik " + "x" * 300 + " pro\ufb01l"
    assert any("bitişik" in h for h in denetle(metin, 1, None, [], 2)["hatalar"])


def test_ats_ikon_fontu_yakalanir():
    metin = "Deneyim Eğitim Yetkinlik " + "x" * 300 + " \uf09b github"
    assert any("özel kullanım" in h for h in denetle(metin, 1, None, [], 2)["hatalar"])


def test_ats_turkce_bozulmasi(profil):
    metin = "Ayse Yilmaz ayse.yilmaz@example.com +90 555 000 00 00 Deneyim Eğitim Yetkinlik " + "x" * 300
    hatalar = denetle(metin, 1, profil, [], 2)["hatalar"]
    assert any("Türkçe karakter" in h for h in hatalar)


def test_ats_bos_metin_ve_sayfa_siniri():
    hatalar = denetle("", 3, None, [], 2)["hatalar"]
    assert any("metin çıkmadı" in h for h in hatalar) and any("3 sayfa" in h for h in hatalar)


def test_ats_anahtar_kelime_siniri():
    metin = "Deneyim Eğitim Yetkinlik JavaScript, C++, C#, Node.js ve REST API " + "x" * 300
    s = denetle(metin, 1, None, ["Java", "JavaScript", "C++", "C#", "C", "node.js", "rest api"], 2)
    assert "Java" in s["eksik"] and "C" in s["eksik"]
    assert {"JavaScript", "C++", "C#", "node.js", "rest api"} <= set(s["bulunan"])


# --- Uçtan uca derleme (LuaLaTeX ve poppler varsa) ---

@pytest.mark.skipif(not (shutil.which("lualatex") and shutil.which("pdftotext")), reason="lualatex/poppler yok")
def test_derleme_ozel_karakter_ve_ats(tmp_path, profil):
    profil["deneyim"][0]["maddeler"].append("R&D ekibinde %30 hız artışı, snake_case API, C# ve $ maliyet {analizi}.")
    profil["projeler"][0]["link"] = "https://github.com/ornek-ayse/kutuphane_v2#readme"
    (tmp_path / "cv.tex").write_text(uret(profil), encoding="utf-8")
    for _ in range(2):
        r = subprocess.run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", "cv.tex"],
                           cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:]
    pdf = str(tmp_path / "cv.pdf")
    metin = pdf_metni(pdf)
    assert "R&D ekibinde %30" in metin and "snake_case" in metin
    sonuc = denetle(metin, sayfa_sayisi(pdf), profil, ["FastAPI", "PostgreSQL"], 2)
    assert sonuc["hatalar"] == [], sonuc
