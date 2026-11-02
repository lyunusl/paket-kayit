# Paket Kayıt

E-ticaret satıcıları için paketleme videosu kaydı. Her siparişin paketlenmesi, sipariş barkoduyla adlandırılmış ayrı bir videoya kaydedilir. İade ya da "eksik ürün geldi" itirazında o siparişin videosu barkodla saniyeler içinde bulunur ve indirilir.

[AugeLab Studio](https://augelab.de) üzerinde çalışan açık kaynak bir senaryodur. Developed by **AugeLab**.

> English summary at the bottom.

## İndir

**[PaketKayit-v1.0.0.zip](https://github.com/lyunusl/paket-kayit/releases/latest)** · Son sürüm her zaman bu linktedir.

Zip'i açın ve `PaketKayit-Kurulum.bat` dosyasına çift tıklayın. Ayrıntılar aşağıda, [Kurulum](#kurulum) bölümünde.

---

## Ne yapar?

- **Barkodla kayıt:** Kargo/sipariş barkodu okutulunca kayıt başlar. Bir sonraki sipariş barkodu okutulunca önceki kayıt kapanır ve yenisi başlar. Barkod gelmezse kayıt azami süre dolunca biter.
- **İki okuma yolu:**
  - Barkod kameradan okunur. Okumayı zbar yapar; AugeLab'ın Barcode Reader bloğunun kullandığı motor da budur. zbar yoksa okumayı OpenCV üstlenir. Bulunan barkod ekranda ve videoda yeşil kare içine alınır.
  - USB barkod okuyucu da kullanılabilir. Okuyucu, açık duran Paket Kayıt sayfasına yazar.
- **Ürün sayımı:** Kayıt sırasında okutulan EAN/UPC ürün barkodları sayılır ve videoya yazılır.
- **Videonun üstündeki bilgi:** Sipariş barkodu, tarih-saat, masa adı ve ürün sayısı videonun sol üstüne işlenir.
- **Sesli uyarı:** Her okumada bip sesi çalar ve ekranda "Okundu: …" bildirimi çıkar.
- **Arşiv:** Kayıtlar barkodla aranır, tarayıcıda izlenir ve tek tıkla indirilir.
- **Saklama:** Belirlenen günden eski kayıtlar otomatik silinir.
- **Ayarlar sayfası:** Masa, kamera, kayıt ve barkod kuralları tarayıcıdan değiştirilir.

## Ekranlar

Senaryo çalışınca tarayıcıda `http://127.0.0.1:8080` adresinde açılır.

| Sekme | İçerik |
|---|---|
| **Paketleme** | Canlı görüntü, ● KAYIT işareti, kalan süre çubuğu, şu anki sipariş ve ürün sayısı, bugün paketlenen sipariş sayısı, son kayıtlar |
| **Kayıtlar** | Barkodun tamamıyla ya da bir kısmıyla arama, videoyu tarayıcıda izleme, **İndir** |
| **Ayarlar** | Aşağıdaki tablodaki tüm ayarlar |

## Gereksinimler

- 64 bit Windows 10/11 (Studio 3.12.0 ile denendi)
- AugeLab Studio. Kurulu değilse kurulum dosyası kendisi indirip kurar. Studio'yu açmak için [account.augelab.com](https://account.augelab.com) hesabınızdaki doğrulama kodu gerekir.
- USB kamera (paketleme masasını yukarıdan gören bir webcam yeterli)
- İsteğe bağlı: USB barkod okuyucu (klavye gibi çalışan her model)
- Chrome veya Edge

## Kurulum

1. Paketi indirin, zip'e sağ tıklayıp **Tümünü ayıkla** deyin ve açılan klasördeki **`PaketKayit-Kurulum.bat`** dosyasına çift tıklayın.
   > Windows "Windows bilgisayarınızı korudu" ya da "Yayımcı doğrulanamadı" uyarısı gösterirse **Ek bilgi → Yine de çalıştır** (veya **Çalıştır**) deyin. Uyarı, dosya internetten indirildiği için çıkar.

   Kurulum şunları yapar:
   - **Visual C++:** Bilgisayarda Microsoft Visual C++ çalışma zamanı yoksa önce Microsoft'un resmi paketini indirir, imzasını doğrular ve kurar. Windows bir kez yönetici izni ister; "Evet" deyin.
   - **Studio:** Kurulu değilse resmi kurulum dosyasını AugeLab sunucusundan indirir, SHA-256 ile doğrular ve sessizce kurar. Başlamadan önce onay sorulur. Temiz bir Windows'ta tüm kurulum yaklaşık 10–15 dakika sürer; Studio'nun Python ve kütüphaneleri indirilir.
   - **Barkod motoru:** Studio'nun zbar motoru (`pyzbar`) Microsoft Visual C++ 2013 çalışma zamanı ister; temiz Windows'ta bu yoktur. Kurulum, zbar çalışmıyorsa önce Visual C++ 2013'ü Microsoft'tan indirir, imzasını doğrular ve kurar; Windows yine yönetici izni ister. zbar hâlâ çalışmazsa PyPI'daki resmi `pyzbar` paketini (SHA-256 doğrulamalı) ekler. Bu adım başarısız olursa kurulum durmaz, okumayı OpenCV yapar.
   - **Bloklar:** Altı Paket Kayıt bloğunu Studio'ya kopyalar.
   - **Senaryo:** Senaryoyu `Belgeler\PaketKayit\PaketKayit.pmod` olarak yerleştirir.
   - **Kısayollar:** Masaüstüne "Paket Kayıt - Studio" ve "Paket Kayıt - Ekran" kısayollarını ekler.
   - **Açılış:** Studio'yu açar.
2. **Sadece ilk seferde:** Studio lisans ekranı açılırsa [account.augelab.com](https://account.augelab.com) hesabınızdaki doğrulama kodunu girip **VERIFY**'a basın.
3. `Belgeler\PaketKayit\PaketKayit.pmod` dosyasına çift tıklayın ya da Studio'da **File → Open** ile açın. Sonra **Run → Run**'a basın. Tarayıcı `http://127.0.0.1:8080` adresinde açılır.
4. **Ayarlar** sekmesinden masa adını, kamera numarasını ve kayıt klasörünü kontrol edip **Kaydet**'e basın.

Kurulumun ne yapacağını değiştirmeden görmek için: `PaketKayit-Kurulum.bat -DryRun`

Studio daha önce açıksa ve bloklar yeni kurulduysa Studio'yu kapatıp yeniden açın; Studio blokları açılırken yükler.

## Kullanım

1. Paketleme sayfası açık ve seçili olsun. Seçili değilse altta "sayfaya tıklayın" uyarısı çıkar. Sesli uyarı için sayfaya bir kez tıklamak gerekir; tarayıcılar sesi ancak bir tıklamadan sonra açar.
2. Sipariş/kargo barkodunu kameraya gösterin ya da okuyucuyla okutun. Bip sesi gelir, ● KAYIT başlar.
3. Ürünleri kutuya koyarken barkodlarını gösterin; ürün sayısı artar. Bu adım isteğe bağlıdır.
4. Sonraki siparişin barkodunu okutun. Önceki kayıt kapanır, yenisi başlar.

İade geldiğinde **Kayıtlar** sekmesinde barkodu yazın, videoyu açın ve **İndir**'e basın.

## Ayarlar

Ayarlar `%APPDATA%\PaketKayit\ayarlar.json` dosyasında saklanır ve kaydedilince hemen uygulanır. Ayarlar yalnızca Studio'nun çalıştığı bilgisayardan değiştirilebilir.

| Ayar | Varsayılan | Açıklama |
|---|---|---|
| Masa adı | Masa 1 | Videonun üstüne yazılır |
| Kamera numarası | 0 | 0 ilk kamera, 1 ikinci kamera |
| Çözünürlük | 1280 x 720 | 640 x 480 / 1280 x 720 / 1920 x 1080 |
| Barkodu kare içine al | açık | Ekranda ve videoda yeşil çerçeve |
| Kayıt klasörü | C:/PaketKayitlari | Yoksa oluşturulur |
| Azami kayıt süresi | 45 sn | Yeni sipariş barkodu gelmezse kayıt burada biter |
| Saklama süresi | 90 gün | Daha eski kayıtlar silinir; 0 = hiç silme |
| Sipariş barkodu önekleri | (boş) | Virgülle ayrılmış önekler, ör. `TY,7270`. Doluysa sadece bu öneklerle başlayan barkodlar sipariş sayılır |
| Sipariş barkodu en az uzunluk | 8 | Önek yoksa bundan kısa barkodlar sipariş sayılmaz |
| EAN/UPC barkodlarını ürün say | açık | Geçerli EAN-8, UPC-A ve EAN-13 kodları sipariş başlatmaz, ürün sayılır |
| Aynı barkodu yeniden sayma süresi | 5 sn | Kamerada duran barkod bir kez sayılır; bu süre kadar kadrajdan çıkıp dönerse yeniden sayılır |

**Kargo barkodunuz da 13 haneli bir EAN ise** "EAN/UPC barkodlarını ürün say" ayarı onu ürün sanar. Bu durumda kargo barkodunuzun önekini **Sipariş barkodu önekleri** alanına yazın.

### Studio içindeki ayarlar

- **Paket Web Arayüzü** bloğu:
  - Arayüz portu (8080).
  - "Yerel ağdan erişime izin ver" (kapalı). Açılırsa aynı ağdaki cihazlar arayüzü izleyebilir; ayarları değiştiremez.
  - "Başlayınca tarayıcıyı aç" (açık).
- **Paket Barkod Girişi** ve **Paket Web Sayfası** bloklarındaki port, arayüz portuyla aynı olmalı.
- Studio'daki blok ayarları yalnızca ilk varsayılandır. Ayarlar sayfasında kaydedilen değerler bunların yerine geçer.

## Dosyalar

Her kayıt `BARKOD_YYYYAAGG_SSDDSS.mp4` adıyla kaydedilir, ör. `TY1234567890_20261102_141530.mp4`.

- H.264, 1280 × 720.
- 45 saniyelik bir kayıt yaklaşık 10 MB.
- Günde 200 paket yaklaşık 2 GB eder; 90 günlük saklama için yeterli disk ayırın.

Otomatik silme yalnızca bu adlandırmaya uyan `.mp4` dosyalarına dokunur.

## Nasıl çalışır?

```
Paket Kamera ──► Paket Barkod Girişi ◄── tarayıcıdan okutulan barkodlar
                  (kameradan barkod okur, yeşil kareyi çizer)
                                                    │
                                                    ▼
                                         Paket Kayıt Kontrol ──► Write Text On Image ──► Save Video (MP4)
                                                    │                       │
                                                    ▼                       ▼
                              Paket Web Sayfası ─► Paket Web Arayüzü (http://127.0.0.1:8080)
                                                    Paket Kayıt Arşivi (saklama süresi)
```

| Blok | Görevi |
|---|---|
| `PaketKamera` | Kamerayı numarasıyla açar, kopunca yeniden dener |
| `PaketWebGiris` | Kameradan barkod okur (OpenCV), sayfadan okutulanlarla birleştirir, sahte ve tekrar okumaları eler, yeşil kareyi çizer |
| `PaketKayitKontrol` | Sipariş/ürün ayrımı, kaydı başlatma, kapatma ve süre sınırı, videonun üstündeki yazı |
| `PaketKayitArsiv` | Saklama süresinden eski kayıtları siler; Studio HMI'ında arama ve oynatma |
| `PaketWebSayfasi` | Arayüz sayfası ve ayarlar |
| `PaketWebArayuz` | Yerel web sunucusu, canlı görüntü, arama, oynatma, indirme |

## Bilinen kısıtlar

- **Bu bir delil sistemi değildir.** Videolar sıradan MP4 dosyalarıdır, değiştirilmediklerine dair imza taşımaz. Pazaryeri itirazlarında destekleyici kayıt olarak kullanın, orijinal dosyaları saklayın.
- **Yeni sipariş sonrası kısa boşluk:** Önceki kayıt açıkken yeni sipariş barkodu okutulursa, eski dosyanın kapanması için yeni kayıt yaklaşık 1 saniye sonra başlar.
- **Barkoddan önceki anlar kaydedilmez.** Kayıt barkod okunduğu anda başlar.
- **Senaryoyu kayıt sırasında durdurmak:** Açık dosya ancak senaryo bir sonraki çalıştırıldığında kapanır. Kayıt bitmeden senaryoyu durdurmayın.
- **Kameradan okuma için barkod net ve yeterince büyük görünmeli.** Desenli yüzeylerden (örgü, kablo) çıkan sahte okumaları elemek için bir kod, 1,5 saniye içinde zbar ile en az 2, OpenCV ile en az 3 karede aynı okunmadıkça sayılmaz. Barkodu kameraya yaklaşık yarım saniye tutun. Hızlı tempo için USB barkod okuyucu önerilir.
- **Temiz Windows'ta Studio'nun zbar'ı çalışmaz.** Studio `pyzbar`'ı kuruyor, ama zbar'ın DLL'i Visual C++ 2013 çalışma zamanı (`msvcr120.dll`) istiyor ve Studio'nun kurulumu bunu eklemiyor. O zaman Studio, AugeLab'ın Barcode Reader bloğunu da yükleyemiyor ("OpCode 342 is not registered"). Paket Kayıt kurulumu bu yüzden Visual C++ 2013'ü kendisi ekler.
- **USB okuyucu sadece sayfa seçiliyken çalışır.** Başka bir pencere öndeyse okutulan barkod kaydedilmez.
- **Studio kurulum dosyası sabitlenmiştir.** `kurulum/studio-installer.json` belirli bir Studio sürümünün SHA-256 özetini içerir. AugeLab yeni bir Studio yayınlayınca bu özet güncellenmeden kurulum Studio'yu indirmez ve hiçbir şey çalıştırmaz. Studio zaten kuruluysa bu adım atlanır.
- **Studio HMI dışa aktarımını depoya koymayın.** Studio'nun HMI dışa aktarma klasörü bilgisayara özel yollar ve kurulumunuza ait bir doğrulama kodu içerir.

## Gizlilik (KVKK)

Kamera paketleme masasını kaydeder. Çalışanlarınızı kayıt hakkında bilgilendirin ve kamerayı yüzleri değil masayı görecek şekilde konumlandırın. Kayıtlar yalnızca bu bilgisayarda tutulur; hiçbir yere gönderilmez.

## Lisans

[MIT](LICENSE) · Copyright (c) 2026 AugeLab

Kodu serbestçe kullanabilir, değiştirebilir ve dağıtabilirsiniz. Tek şart, telif satırının ve lisans metninin kopyalarda korunmasıdır.

AugeLab adı ve logosu bu lisansa dahil değildir. Değiştirilmiş sürümleri AugeLab ürünü olarak sunmayın.

---

## English summary

**Paket Kayıt** records a separate video for every packed e-commerce order, named after the order/shipping barcode, so returns and "missing item" disputes can be answered by searching the barcode and downloading the clip.

- It runs as a scenario in [AugeLab Studio](https://augelab.de) with six custom blocks.
- Barcodes are read from the camera with zbar (pyzbar, the engine behind AugeLab's Barcode Reader; on a clean Windows it needs the Visual C++ 2013 runtime, which the setup installs), falling back to OpenCV, with a green box drawn around them; codes must repeat across frames to count. A USB scanner typing into the local web page also works.
- An order barcode starts a recording; the next order barcode closes it. EAN/UPC product codes scanned during a recording are counted.
- The local web UI at `http://127.0.0.1:8080` has three tabs: live packing view with recording state and a beep per scan, recording search with playback and download, and settings.
- Install: run `PaketKayit-Kurulum.bat`. It installs AugeLab Studio when missing (official installer, SHA-256 verified, silent), copies the blocks and the scenario, adds desktop shortcuts and starts Studio. On first use, activate Studio with the key from account.augelab.com, open `Documents\PaketKayit\PaketKayit.pmod` and press Run.
- License: [MIT](LICENSE), Copyright (c) 2026 AugeLab. The AugeLab name and logo are not covered by the license.

Developed by **AugeLab**.
