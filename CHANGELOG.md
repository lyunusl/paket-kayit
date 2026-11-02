# Değişiklikler

## v1.0.0 · 2026-11-02

İlk sürüm.

- **Barkodla kayıt:** Sipariş barkodu okutulunca kayıt başlar, bir sonraki sipariş barkodunda ya da azami sürede kapanır. Videonun adı `BARKOD_YYYYAAGG_SSDDSS.mp4` olur.
- **Barkod okuma:**
  - Kameradan zbar ile okunur; AugeLab'ın Barcode Reader bloğunun kullandığı motor da budur. zbar yoksa OpenCV devreye girer.
  - USB barkod okuyucu da kullanılabilir.
  - Sahte okumalar filtrelenir ve okunan barkod yeşil kare içine alınır.
- **Ürün sayımı:** EAN/UPC ürün barkodları sayılır. Videonun üstüne barkod, tarih-saat, masa adı ve ürün sayısı yazılır.
- **Web arayüzü** (`http://127.0.0.1:8080`):
  - **Paketleme:** canlı görüntü, kayıt durumu, bip sesi.
  - **Kayıtlar:** arama, izleme, indirme.
  - **Ayarlar.**
- **Kamera:** Kamera numarasıyla açılır. Kamera yoksa ekranda "Kamera bulunamadı" görünür.
- **Saklama:** Belirlenen günden eski kayıtlar otomatik silinir.
- **Tek tıkla kurulum (`PaketKayit-Kurulum.bat`):**
  - Microsoft Visual C++ (2015–2022 ve 2013) ile AugeLab Studio'yu gerekirse indirip doğrular ve kurar.
  - Blokları, senaryoyu ve masaüstü kısayollarını yerleştirir.
  - Temiz bir Windows 11'de (Windows Sandbox) baştan sona test edildi.

### Bilinen kısıtlar

- Studio lisansı (account.augelab.com) ilk açılışta elle girilir.
- Kurulum, AugeLab Studio 3.12.0'ın kurulum dosyasına SHA-256 ile sabitlenmiştir. Yeni Studio sürümleri için Paket Kayıt'ın da güncellenmesi gerekir.
- Kurulum dosyaları imzasızdır. Windows indirilen dosya için uyarı gösterebilir.
