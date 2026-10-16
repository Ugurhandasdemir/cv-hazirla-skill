# Soru kalıpları ve madde yazımı

## Bölüm bölüm sorular

### Kişisel
- CV'de adın nasıl yazılsın? Unvan satırında ne yazsın?
- İletişim e-postan, telefonun (+90 ile), şehrin?
- LinkedIn, GitHub ya da portfolyo adresin var mı?

### Özet
Adaydan hazır özet isteme, malzeme iste:
1. Hangi alanda çalışıyorsun ya da çalışmak istiyorsun? (ör. backend, veri bilimi, gömülü, ürün)
2. En iyi bildiğin 2-3 teknoloji ya da beceri hangisi?
3. Seni diğer adaylardan ayıran bir iş, proje ya da sonuç var mı?
4. Nasıl çalışmayı seversin, ya da kısa vadede neye odaklanmak istiyorsun?

Taslağı yazıp adaya göster: "Şöyle yazdım, eklemek ya da çıkarmak istediğin var mı?"

### İş deneyimi ve staj (her kayıt için)
- Kurum adı, şehir (ya da uzaktan), pozisyon adı, çalışma şekli (tam zamanlı, yarı zamanlı, hibrit, uzaktan)?
- Başlangıç ve bitiş tarihi (AA/YYYY)? Hâlâ sürüyorsa "devam".
- Orada ne yaptın? Hangi problemi çözdün?
- Hangi araç, dil, framework kullandın?
- Sonuç ne oldu? Bir sayı var mı: süre, adet, kullanıcı, hata oranı, maliyet, doğruluk?
- Ekip içinde senin payın neydi? (Ekip işi ise "ekiple birlikte ... geliştirdik, ben ... kısmını yaptım")

### Eğitim
- Okul, bölüm, derece (lisans, ön lisans, yüksek lisans), şehir?
- Başlangıç ve (beklenen) bitiş tarihi? Mezun musun, öğrenci misin?
- GANO yazılsın mı? (Genel kural: 3.00/4.00 ve üstüyse yazılması faydalı, altındaysa adaya bırak.)
- Değişim programı, çift anadal, yan dal, onur derecesi?

### Projeler
- Projenin kısa adı, ne işe yarıyor?
- Senin katkın ne? Tek başına mı, ekiple mi?
- Hangi teknolojiler?
- Kullanan oldu mu, bir derece aldı mı, ölçülen bir sonuç var mı?
- GitHub ya da demo linki?

### Yetkinlikler
- Hangi programlama dillerini gerçekten kullandın? (Bir dersten bir ödev yeterli sayılmaz, proje ya da işte kullanım)
- Framework, kütüphane, veritabanı, bulut, araçlar?

### Başarılar, sertifikalar, diller, topluluk
- Yarışma derecesi, burs, ödül? Hangi yıl?
- Sertifika adı, veren kurum, tarih?
- Yabancı dil ve seviyesi (CEFR: A1-C2, ya da YDS/IELTS/TOEFL puanı)?
- Kulüp, takım, gönüllülük görevi? Rol ve tarih aralığı?

## Madde yazımı

Kalıp: **geçmiş zaman fiili + ne + nasıl/hangi araçla + sonuç**

| Zayıf | Güçlü |
|---|---|
| Backend tarafında görev aldım. | FastAPI ile sipariş takibi için 12 uçlu bir REST servisi geliştirdim. |
| Raporlarla ilgilendim. | Oracle SQL'deki 500'den fazla raporu inceleyip yavaş sorguları düzenledim. |
| Veri analizi yaptım. | pandas ile 2 yıllık satış verisini temizleyip haftalık talep tahmini çıkardım, hata oranı %18'den %9'a indi. |
| Takıma yardımcı oldum. | Ekibin test sürecine birim testleri ekledim, kapsamayı %40'tan %75'e çıkardım. |

Kurallar:
- Sayı adaydan gelmediyse cümleyi sayısız bırak. "Yaklaşık" bile uydurma sayılır.
- Bir madde 1-2 satır. Uzun maddeyi ikiye böl.
- Aynı fiili art arda kullanma (geliştirdim, geliştirdim, geliştirdim). Alternatifler: tasarladım,
  kurdum, otomatikleştirdim, düzenledim, ölçtüm, taşıdım, hızlandırdım, entegre ettim, test ettim.
- İngilizce CV'de: past tense action verb ile başla (Built, Designed, Reduced, Automated), özne yok.

## ATS ile ilgili kısa notlar

- ATS'ler PDF'i düz metne çevirip bölüm başlıklarından alan ayırır. Yaratıcı başlık ("Yolculuğum")
  yerine standart başlık ("İş Deneyimi") kullan.
- İki sütunlu düzen, tablo ve metin kutusu okuma sırasını bozar. Şablon tek sütundur.
- İkon fontları (telefon, e-posta simgeleri) çöp karakter olarak okunur. Şablonda ikon yoktur.
- "fi", "fl" bitişik harfleri bazı yazı tiplerinde tek karakter (ﬁ) olarak gömülür ve "profil"
  kelimesi aramada bulunmaz. Şablonda ligatür kapalıdır, `ats_kontrol.py` bunu ayrıca denetler.
- Anahtar kelime eşleşmesi çoğu ATS'de birebir yazıma bakar. İlanın yazımını kullan
  ("Node.js" ise "NodeJS" değil), kısaltmayı ilk geçtiği yerde açık haliyle de yaz gerekirse
  ("Makine Öğrenmesi (ML)").
- Tarihleri her yerde aynı biçimde yaz (AA/YYYY). Karışık biçim deneyim süresi hesabını bozar.
