---
name: cv-hazirla
description: Bir adayla soru-cevap yaparak sıfırdan ya da mevcut CV'sinden ATS uyumlu, tek sütunlu bir LaTeX/PDF CV hazırlar. Özet, iş deneyimi, staj, eğitim, projeler, yetkinlikler, başarılar, sertifikalar ve dilleri doldurur; eksik bilgiyi (ör. staj tarihi, ölçülebilir sonuç) adaya sorar, asla uydurmaz. İsteğe bağlı olarak bir iş ilanına göre vurguyu ayarlar. "CV hazırla", "özgeçmiş oluştur", "CV'mi düzelt", "ATS uyumlu CV", "arkadaşıma CV yapalım" dendiğinde ya da bir CV dosyası paylaşılıp düzenlenmesi istendiğinde kullan.
---

# CV Hazırla

Adayla konuşarak tam bir CV çıkarırsın. Tek doğruluk kaynağı adayın verdiği bilgidir. Sen yazıyı
toparlar, eksikleri sorar, ATS'nin okuyacağı biçime sokarsın. Bilmediğin hiçbir şeyi (tarih,
sayı, unvan, teknoloji, sonuç) tahminle doldurmazsın.

`$SKILL_DIR` bu dosyanın bulunduğu klasördür. Scriptler yalnız Python standart kütüphanesi kullanır.
Derleme için LuaLaTeX (ya da XeLaTeX), ATS denetimi için poppler-utils (`pdftotext`, `pdfinfo`) gerekir.

## Çalışma düzeni

Her aday için bir çalışma klasörü aç (ör. `cv-<ad-soyad>/`). İçinde:

| Dosya | Ne |
|---|---|
| `profil.json` | Adayın bütün bilgisi. Şema: `$SKILL_DIR/examples/ornek-profil.json` |
| `ilan.txt` | (isteğe bağlı) Hedef iş ilanı |
| `cv.tex`, `cv.pdf` | Üretilen CV |

`profil.json`'u sen yazarsın ama içindeki her değer adaydan gelir. Adayın verdiği ham bilgiyi
madde cümlesine çevirmek senin işin. Cümleye bilgi eklemek değil.

## Adımlar

### 1. Başlangıç bilgisini al

Adaya kısaca sor:
- Elinde mevcut bir CV var mı (PDF, DOCX, metin, LinkedIn çıktısı)? Varsa onu iste.
- Hedef pozisyon ya da alan ne? Belirli bir ilan var mı? Varsa metnini ya da linkini iste.
- CV Türkçe mi İngilizce mi olacak? (`dil`: `tr` ya da `en`)

Mevcut CV varsa oku (PDF için `pdftotext -layout dosya.pdf -`) ve bilgileri `profil.json`'a aktar.
Aktarırken yorum katma. Belirsiz olanı (ör. "2024 yazı" gibi tarih) boş bırak, soruda netleştirirsin.
CV yoksa `profil.json`'u boş şemayla başlat.

### 2. Eksikleri bul

```bash
python3 "$SKILL_DIR/scripts/eksik.py" profil.json
```

Script her bulguyu bir seviye ve hazır bir soruyla verir:
- `zorunlu`: Bu bilgi olmadan CV üretilmez. Örnek: stajın başlangıç ve bitiş tarihi, e-posta, eğitim.
- `hata`: Bilgi var ama geçersiz. Örnek: bitiş tarihi başlangıçtan önce, okunamayan tarih, emoji.
- `oneri`: CV'yi güçlendirir. Aday "yok" ya da "istemiyorum" derse atlanır. Örnek: ölçülebilir sonuç, GANO, LinkedIn.

Script'in bulamadığı şeyleri de sen kontrol et: maddeler gerçekten adayın katkısını mı anlatıyor,
özet hedef pozisyona uyuyor mu, ilanın istediği bir beceri adayda olup CV'de yazmıyor mu.

### 3. Adaya sor (mülakat)

Kurallar:
- **Bir turda en çok 5 soru sor.** Önce `hata`, sonra `zorunlu`, en son `oneri`. Aynı kayda ait soruları
  birleştir: "Örnek A.Ş. stajın: başlangıç ve bitiş tarihi (AA/YYYY), şehir, orada yaptığın 2-3 somut iş?"
- Soruyu adayın diliyle, kısa ve somut sor. Ne biçimde cevap beklediğini yaz (AA/YYYY, "devam").
- Adayın cevabını `profil.json`'a işle, sonra `eksik.py`'yi yeniden çalıştır. `zorunlu` ve `hata`
  kalmayana kadar tura devam et.
- Aday bir `oneri`yi reddederse ya da bilmiyorsa o alanı boş bırak ve bir daha sorma.
- Aday bir `zorunlu` bilgiyi bilmiyorsa (ör. staj ayını hatırlamıyor) yalnız yılı yazmayı öner.
  Hiç bilinmiyorsa o kaydı CV'ye koyup koymamayı adaya sor, kendin karar verme.

Ölçülebilir sonuç sorusu en değerli sorudur. Aday "rapor hazırladım" dediyse "kaç rapor, ne kadar
sürede, ne işe yaradı?" diye sor. Cevap yoksa madde sayısız kalır, sayı uydurulmaz.

Ayrıntılı soru kalıpları ve madde yazımı: `$SKILL_DIR/references/soru-ve-yazim.md`.

### 4. Bölümleri yaz

- **Özet** 3-4 cümle, yaklaşık 400-600 karakter, birinci tekil kişi ("çalışıyorum", "geliştirdim").
  İlk cümle: alan ve seviye. İkinci: en güçlü 2-3 beceri ve somut kanıt. Üçüncü: çalışma tarzı ya da hedef.
  Taslağı adaya göster ve onayını al.
- **Deneyim/staj maddeleri:** her kayıtta 2-4 madde. Kalıp: geçmiş zaman fiili + ne yapıldı + hangi
  araçla + sonuç. "Görev aldım", "yardımcı oldum" gibi edilgen kalıplardan kaçın.
- **Yetkinlikler:** kategorilere böl (Diller, Framework, Veritabanı, Araçlar gibi). Yalnız adayın
  gerçekten kullandıklarını yaz. Seviye çubuğu, yıldız, yüzde koyma.
- **Projeler:** 2-5 proje, en güçlüsü üstte. Her projede 1-3 madde ve teknoloji satırı.
- **Bölüm sırası** (`bolum_sirasi`): deneyimi olan aday için deneyim önce. Yeni mezun ya da
  öğrenci için eğitim ve projeler öne alınabilir. Güçlü bir yarışma derecesi varsa başarılar
  özetin hemen altına çıkabilir.

### 5. (İsteğe bağlı) İlana göre ayarla

İlan varsa ilandaki teknik şartları ve anahtar kelimeleri çıkar. Sonra:
- Unvan satırını ilanın pozisyon adına yaklaştır (adayın gerçek seviyesini aşmadan).
- Özetin ilk cümlesine ilanın istediği ve adayda olan yetkinlikleri taşı.
- Yetkinlik satırlarını ilandaki sıraya göre diz. İlanın istediği ama adayda olmayan beceriyi ekleme.
- İlanın kullandığı terimi adayın da yaptığı işe uyuyorsa aynen kullan (ilan "REST API" diyorsa "web servisi" değil).
- Zorunlu bir şart karşılanmıyorsa (ör. "en az 3 yıl deneyim") CV'yi yazmadan önce adaya söyle.

### 6. Üret ve derle

```bash
python3 "$SKILL_DIR/scripts/render.py" profil.json -o cv.tex
lualatex -interaction=nonstopmode -halt-on-error cv.tex >/dev/null
lualatex -interaction=nonstopmode -halt-on-error cv.tex | grep "Output written"
```

`render.py` eksik zorunlu bilgi varsa üretmez ve neyin eksik olduğunu yazar. Taslak görmek için
`--zorla` kullanılabilir ama adaya verilen son CV'de kullanılmaz.
Liberation Sans kurulu değilse `--font "DejaVu Sans"` gibi kurulu bir yazı tipi ver
(`fc-list | grep -i sans`). Derleme çöpünü (`.aux`, `.log`) aday klasörüne değil geçici klasöre bırakmak istersen derlemeyi orada yap.

### 7. ATS denetimi

```bash
python3 "$SKILL_DIR/scripts/ats_kontrol.py" cv.pdf --profil profil.json --anahtar "Python,Docker,REST API"
```

`--anahtar` listesini ilandan sen çıkarırsın (ilan yoksa atla). Script PDF'i ATS gibi düz metne
çevirir ve şunları denetler: metin çıkıyor mu, ad/e-posta/telefon birebir okunuyor mu, Türkçe
karakterler bozuluyor mu, bitişik harf (ligatür) ya da ikon fontu var mı, standart başlıklar var mı,
sayfa sınırı (varsayılan 2, yeni mezun için `--max-sayfa 1` öner) ve anahtar kelime kapsaması.

`[HATA]` kalmayana kadar düzelt. Eksik anahtar kelimeyi yalnız aday o beceriye gerçekten sahipse ekle.

Ayrıca PDF'i aç ve gözle kontrol et (`pdftoppm -png -r 80 cv.pdf sayfa` ile görüntüye çevirip bak):
- Sayfa sınırı aşıldıysa önce madde uzunluklarını kısalt, sonra en zayıf projeyi çıkarmayı **adaya öner**.
- Uzun proje başlığı sağdaki linke yapışıyorsa başlığı kısalt.

### 8. Teslim et ve raporla

Adaya şunları söyle:
- PDF'in yolu ve sayfa sayısı
- ATS denetimi sonucu, ilan varsa anahtar kelime kapsaması
- Boş bırakılan `oneri` alanları (aday sonra eklemek isterse)
- İlandaki karşılanmayan şartlar

Dosya adı önerisi: `Ad_Soyad_CV.pdf` (Türkçe karakter korunabilir, boşluk yerine alt çizgi).

## Kesin kurallar

- **Uydurma yok.** Tarih, sayı, yüzde, şirket adı, unvan, teknoloji, ödül adaydan gelmediyse CV'ye girmez.
  Madde cümlesini güzelleştirebilirsin ama yeni bilgi ekleyemezsin.
- **Staj ve kulüp çalışmasını "iş deneyimi" diye şişirme.** `tur` alanı doğru yazılır, pozisyon adında
  "Stajyer" kalır.
- **ATS biçimi:** tek sütun, tablo yok, ikon/emoji/fotoğraf yok, standart bölüm başlıkları, tarih
  biçimi her yerde AA/YYYY, linkler açık metin olarak görünür. Şablon bunları zaten sağlar, elle
  `cv.tex`'e tablo ya da ikon ekleme.
- **Kişisel veri:** adayın telefonunu, adresini, TC kimlik numarasını gereksiz yere isteme.
  TC kimlik no, doğum tarihi, medeni durum, fotoğraf ATS CV'sinde yer almaz. Aday özellikle isterse
  bunun genelde gerekmediğini söyle.
- Adayın bilgisini başka bir yere (repo, issue, sohbet dışı servis) adayın onayı olmadan gönderme.
