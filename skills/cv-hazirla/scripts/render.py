#!/usr/bin/env python3
"""profil.json'dan ATS uyumlu, tek sütunlu LaTeX CV üretir.

Kullanım:
    python3 render.py profil.json -o cv.tex
    python3 render.py profil.json -o cv.tex --zorla     # eksik varken de üret (taslak için)

Derleme (LuaLaTeX ya da XeLaTeX):
    lualatex -interaction=nonstopmode -halt-on-error cv.tex

Eksik zorunlu alan veya hatalı veri varsa üretmez, eksik.py'nin sorularını basar.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from eksik import kontrol_et
from ortak import bos_mu, devam_mi, profil_oku

BASLIKLAR = {
    "tr": {
        "ozet": "Profesyonel Özet",
        "deneyim": "İş Deneyimi",
        "egitim": "Eğitim",
        "yetkinlikler": "Teknik Yetkinlikler",
        "projeler": "Projeler",
        "basarilar": "Yarışmalar ve Başarılar",
        "sertifikalar": "Sertifikalar",
        "diller": "Yabancı Diller",
        "topluluk": "Liderlik ve Topluluk Deneyimi",
        "devam": "Devam ediyor",
        "teknolojiler": "Teknolojiler",
        "gano": "GANO",
        "mezun": "Mezun",
        "ogrenci": "Öğrenci",
        "babel": "turkish",
    },
    "en": {
        "ozet": "Summary",
        "deneyim": "Experience",
        "egitim": "Education",
        "yetkinlikler": "Skills",
        "projeler": "Projects",
        "basarilar": "Awards",
        "sertifikalar": "Certifications",
        "diller": "Languages",
        "topluluk": "Leadership and Activities",
        "devam": "Present",
        "teknolojiler": "Technologies",
        "gano": "GPA",
        "mezun": "Graduated",
        "ogrenci": "Student",
        "babel": "english",
    },
}

VARSAYILAN_SIRA = ["ozet", "deneyim", "egitim", "yetkinlikler", "projeler", "basarilar", "sertifikalar", "diller", "topluluk"]

_KACIS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def kac(metin) -> str:
    """Düz metni LaTeX'e güvenle yazar. None ve sayı da kabul edilir."""
    if metin is None:
        return ""
    return "".join(_KACIS.get(c, c) for c in str(metin).strip())


def url_kac(url: str) -> str:
    """\\href'in ilk argümanı: yalnız % ve # kaçırılır, hyperref gerisini çözer."""
    return url.strip().replace("\\", "").replace("%", r"\%").replace("#", r"\#")


def url_metni(url: str) -> str:
    s = url.strip()
    for on in ("https://", "http://"):
        if s.startswith(on):
            s = s[len(on):]
    if s.startswith("www."):
        s = s[4:]
    return s.rstrip("/")


def url_tam(url: str) -> str:
    s = url.strip()
    if s.startswith("mailto:") or "://" in s:
        return s
    return "https://" + s


def link(url: str) -> str:
    return rf"\href{{{url_kac(url_tam(url))}}}{{{kac(url_metni(url))}}}"


ONSOZ = r"""\documentclass[10pt,a4paper]{article}

% LuaLaTeX veya XeLaTeX ile derleyin. Tek sütun, tablo ve ikon yok: ATS düz metin olarak okur.
\usepackage{fontspec}
\usepackage[<<babel>>]{babel}
\setmainfont{<<font>>}[Ligatures=NoCommon]

\usepackage[a4paper,left=13mm,right=13mm,top=11mm,bottom=11mm]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks,pdftitle={<<pdftitle>>},pdfauthor={<<pdfauthor>>}]{hyperref}
\usepackage{titlesec}
\usepackage[protrusion=false]{microtype}
\usepackage{xcolor}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\pagestyle{empty}
\urlstyle{same}

\definecolor{heading}{HTML}{1A1A1A}

\titleformat{\section}
  {\large\bfseries\color{heading}}
  {}{0pt}{}
  [\vspace{1pt}\titlerule]
\titlespacing*{\section}{0pt}{5pt}{3pt}

\setlist[itemize]{leftmargin=4.5mm, itemsep=1.5pt, topsep=2pt, parsep=0pt, partopsep=0pt}

\newcommand{\roleentry}[4]{%
  \textbf{#1} \hfill #2\\
  \textit{#3} \hfill \textit{#4}\par\vspace{1pt}
}

\newcommand{\projectentry}[2]{%
  \textbf{#1}\hfill #2\par\vspace{-1pt}
}

\begin{document}
"""


class Cizici:
    def __init__(self, profil: dict, font: str) -> None:
        self.p = profil
        self.dil = profil.get("dil", "tr") if profil.get("dil") in BASLIKLAR else "tr"
        self.t = BASLIKLAR[self.dil]
        self.font = font
        self.satirlar: list[str] = []

    def y(self, s: str = "") -> None:
        self.satirlar.append(s)

    def aralik(self, kayit: dict) -> str:
        bas, bit = kayit.get("baslangic"), kayit.get("bitis")
        if bos_mu(bas) and bos_mu(bit):
            return ""
        bit_s = self.t["devam"] if devam_mi(bit) else (bit or "")
        if bos_mu(bas):
            return kac(bit_s)
        return f"{kac(bas)} -- {kac(bit_s)}" if bit_s else kac(bas)

    def maddeler(self, maddeler) -> None:
        temiz = [m for m in (maddeler or []) if isinstance(m, str) and not bos_mu(m)]
        if not temiz:
            return
        self.y(r"\begin{itemize}")
        for m in temiz:
            self.y(rf"  \item {kac(m)}")
        self.y(r"\end{itemize}")

    def teknolojiler(self, tek) -> None:
        if bos_mu(tek):
            return
        self.y(rf"\textit{{{self.t['teknolojiler']}: {kac(', '.join(tek))}}}")

    # --- bölümler ---

    def baslik(self) -> None:
        k = self.p.get("kisisel") or {}
        self.y(r"\begin{center}")
        self.y(rf"  {{\LARGE\textbf{{{kac(k.get('ad_soyad'))}}}}}\\[3pt]")
        if not bos_mu(k.get("unvan")):
            self.y(rf"  {{\large\textbf{{{kac(k.get('unvan'))}}}}}\\[5pt]")
        satir1 = []
        if not bos_mu(k.get("sehir")):
            satir1.append(kac(k["sehir"]))
        if not bos_mu(k.get("telefon")):
            satir1.append(kac(k["telefon"]))
        if not bos_mu(k.get("eposta")):
            e = k["eposta"].strip()
            satir1.append(rf"\href{{mailto:{url_kac(e)}}}{{{kac(e)}}}")
        satir2 = [link(k[a]) for a in ("github", "linkedin", "web") if not bos_mu(k.get(a))]
        if satir1:
            self.y("  " + r" \;|\; ".join(satir1) + (r"\\[2pt]" if satir2 else ""))
        if satir2:
            self.y("  " + r" \;|\; ".join(satir2))
        self.y(r"\end{center}")

    def ozet(self) -> None:
        if bos_mu(self.p.get("ozet")):
            return
        self.y(rf"\section{{{self.t['ozet']}}}")
        self.y(kac(self.p["ozet"]))

    def _rol_listesi(self, anahtar: str) -> None:
        kayitlar = self.p.get(anahtar) or []
        if not kayitlar:
            return
        self.y()
        self.y(rf"\section{{{self.t[anahtar]}}}")
        for i, d in enumerate(kayitlar):
            if i:
                self.y(r"\vspace{3pt}")
            poz = kac(d.get("pozisyon"))
            if not bos_mu(d.get("calisma_sekli")):
                poz += f" / {kac(d['calisma_sekli'])}"
            self.y(rf"\roleentry{{{kac(d.get('kurum'))}}}{{{kac(d.get('sehir'))}}}{{{poz}}}{{{self.aralik(d)}}}")
            self.maddeler(d.get("maddeler"))
            self.teknolojiler(d.get("teknolojiler"))

    def deneyim(self) -> None:
        self._rol_listesi("deneyim")

    def topluluk(self) -> None:
        self._rol_listesi("topluluk")

    def egitim(self) -> None:
        kayitlar = self.p.get("egitim") or []
        if not kayitlar:
            return
        self.y()
        self.y(rf"\section{{{self.t['egitim']}}}")
        for i, e in enumerate(kayitlar):
            if i:
                self.y(r"\vspace{3pt}")
            ust = kac(e.get("bolum"))
            if not bos_mu(e.get("derece")):
                ust += f", {kac(e['derece'])}"
            self.y(rf"\textbf{{{ust}}} \hfill {self.aralik(e)}\\")
            alt = kac(e.get("okul"))
            if not bos_mu(e.get("sehir")):
                alt += f", {kac(e['sehir'])}"
            sag = []
            durum = e.get("durum")
            if durum in ("mezun", "ogrenci"):
                sag.append(self.t[durum])
            if not bos_mu(e.get("gano")):
                sag.append(f"{self.t['gano']}: {kac(e['gano'])}")
            self.y(alt + (rf" \hfill \textbf{{{r' \;|\; '.join(sag)}}}" if sag else ""))
            self.maddeler(e.get("maddeler"))

    def yetkinlikler(self) -> None:
        gruplar = [g for g in (self.p.get("yetkinlikler") or []) if not bos_mu(g.get("ogeler"))]
        if not gruplar:
            return
        self.y()
        self.y(rf"\section{{{self.t['yetkinlikler']}}}")
        satirlar = []
        for g in gruplar:
            ogeler = kac(", ".join(g["ogeler"]))
            satirlar.append(rf"\textbf{{{kac(g['kategori'])}:}} {ogeler}" if not bos_mu(g.get("kategori")) else ogeler)
        self.y("\\\\\n".join(satirlar))

    def projeler(self) -> None:
        kayitlar = self.p.get("projeler") or []
        if not kayitlar:
            return
        self.y()
        self.y(rf"\section{{{self.t['projeler']}}}")
        for i, pr in enumerate(kayitlar):
            if i:
                self.y(r"\vspace{3pt}")
            sag = []
            if not bos_mu(pr.get("odul")):
                sag.append(rf"\textit{{{kac(pr['odul'])}}}")
            if not bos_mu(pr.get("link")):
                sag.append(rf"{{\small {link(pr['link'])}}}")
            self.y(rf"\projectentry{{{kac(pr.get('baslik'))}}}{{{r' \;|\; '.join(sag)}}}")
            self.maddeler(pr.get("maddeler"))
            self.teknolojiler(pr.get("teknolojiler"))

    def basarilar(self) -> None:
        kayitlar = self.p.get("basarilar") or []
        if not kayitlar:
            return
        self.y()
        self.y(rf"\section{{{self.t['basarilar']}}}")
        for i, s in enumerate(kayitlar):
            if i:
                self.y(r"\vspace{3pt}")
            aciklama = s.get("aciklama")
            self.y(rf"\textbf{{{kac(s.get('baslik'))}}} \hfill {kac(s.get('yil'))}" + (r"\\" if not bos_mu(aciklama) else r"\par"))
            if not bos_mu(aciklama):
                self.y(kac(aciklama) + r"\par")

    def sertifikalar(self) -> None:
        kayitlar = self.p.get("sertifikalar") or []
        if not kayitlar:
            return
        self.y()
        self.y(rf"\section{{{self.t['sertifikalar']}}}")
        self.y(r"\begin{itemize}")
        for s in kayitlar:
            ad = rf"\textbf{{{kac(s.get('ad'))}}}"
            if not bos_mu(s.get("kurum")):
                ad += f", {kac(s['kurum'])}"
            self.y(rf"  \item {ad} \hfill {kac(s.get('tarih'))}")
        self.y(r"\end{itemize}")

    def diller(self) -> None:
        kayitlar = self.p.get("diller") or []
        if not kayitlar:
            return
        self.y()
        self.y(rf"\section{{{self.t['diller']}}}")
        self.y(", ".join(f"{kac(d.get('dil'))}: {kac(d.get('seviye'))}" for d in kayitlar))

    def ciz(self) -> str:
        k = self.p.get("kisisel") or {}
        ad = kac(k.get("ad_soyad"))
        onsoz = ONSOZ
        for anahtar, deger in {
            "babel": self.t["babel"],
            "font": self.font,
            "pdftitle": f"{ad} - CV",
            "pdfauthor": ad,
        }.items():
            onsoz = onsoz.replace(f"<<{anahtar}>>", deger)
        self.satirlar = [onsoz]
        self.baslik()
        sira = self.p.get("bolum_sirasi") or VARSAYILAN_SIRA
        bilinmeyen = [s for s in sira if s not in VARSAYILAN_SIRA]
        if bilinmeyen:
            raise ValueError(f"bolum_sirasi içinde bilinmeyen bölüm: {bilinmeyen}")
        for bolum in sira:
            getattr(self, bolum)()
        self.y()
        self.y(r"\end{document}")
        return "\n".join(self.satirlar) + "\n"


def uret(profil: dict, font: str = "Liberation Sans") -> str:
    return Cizici(profil, font).ciz()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profil")
    ap.add_argument("-o", "--cikti", default="cv.tex")
    ap.add_argument("--font", default="Liberation Sans", help="sistemde kurulu yazı tipi (varsayılan Liberation Sans)")
    ap.add_argument("--zorla", action="store_true", help="eksik/hatalı alan varken de üret")
    args = ap.parse_args()

    try:
        profil = profil_oku(args.profil)
    except (OSError, ValueError) as e:
        print(f"profil okunamadı: {e}", file=sys.stderr)
        return 2

    engel = [b for b in kontrol_et(profil, date.today()) if b["seviye"] in ("zorunlu", "hata")]
    if engel and not args.zorla:
        print("CV üretilmedi, önce şu bilgiler tamamlanmalı:", file=sys.stderr)
        for b in engel:
            print(f"  [{b['seviye']}] {b['alan']}: {b['soru']}", file=sys.stderr)
        return 1

    try:
        tex = uret(profil, args.font)
    except ValueError as e:
        print(f"hata: {e}", file=sys.stderr)
        return 2
    with open(args.cikti, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"yazıldı: {args.cikti}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
