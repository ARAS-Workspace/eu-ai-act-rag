# Gizlilik Bildirimi — EU AI Act RAG Playground

**Son Güncelleme:** Şubat 2026

## Genel Bakış

EU AI Act RAG Playground, AB Yapay Zeka Yasası'nı (Yönetmelik 2024/1689) sorgulamak için geliştirilmiş açık kaynaklı, deneysel bir retrieval-augmented generation sistemidir. Bu bildirim, sistemin hangi verileri işlediğini, verilerin nasıl aktığını ve hangi üçüncü taraf hizmetlerin kullanıldığını açıklamaktadır.

Kaynak kodun tamamı, altyapı yapılandırmaları ve CI/CD pipeline'ları bu repository'de herkese açık olarak bulunmaktadır. Üretim dağıtımları doğrudan repository üzerinden GitHub Actions workflow'ları ile tetiklenmektedir.

## Mimari

Sistem aşağıdaki Cloudflare hizmetlerinden oluşmaktadır:

| Hizmet                             | Amaç                                                                                 |
|------------------------------------|--------------------------------------------------------------------------------------|
| **Cloudflare Workers**             | API backend — sohbet isteklerini, hız sınırlamayı ve Turnstile doğrulamasını yönetir |
| **Cloudflare Containers**          | Streamlit playground arayüzünü barındırır                                            |
| **Cloudflare AI Search (AutoRAG)** | AB Yapay Zeka Yasası corpus'u üzerinde vektör arama ve LLM yanıt üretimi             |
| **Cloudflare Workers AI**          | Embedding, reranking, sorgu yeniden yazma ve metin üretim modelleri                  |
| **Cloudflare KV**                  | Hız sınırlama sayaçları için geçici depolama (TTL ile otomatik sona erer)            |
| **Cloudflare R2**                  | AB Yapay Zeka Yasası corpus dokümanları için nesne depolama                          |
| **Cloudflare Turnstile**           | Görünmez bot koruması (Invisible mod)                                                |

## Hangi Veriler İşleniyor?

### Sizin Sağladığınız Veriler

| Veri                  | Amaç                                                  | Nereye Gönderilir                                           |
|-----------------------|-------------------------------------------------------|-------------------------------------------------------------|
| **Sohbet mesajları**  | Yanıt üretimi için Cloudflare Workers AI'a gönderilir | Worker tarafından bellekte işlenir, kalıcı olarak saklanmaz |
| **Dil tercihi**       | Yanıt dilini belirler (İngilizce veya Türkçe)         | API isteğinin bir parçası olarak gönderilir                 |
| **Arama seçenekleri** | Model seçimi, sonuç sayısı, puan eşiği                | API isteğinin bir parçası olarak gönderilir                 |

### Otomatik Olarak İşlenen Veriler

| Veri                          | Amaç                                                                     | Saklama Süresi                                                                                |
|-------------------------------|--------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **IP adresi (hız sınırlama)** | IP başına hız sınırlarını uygular (5/dk, 30/saat, 100/gün)               | Cloudflare KV'de TTL ile saklanır — sona erme sonrası otomatik silinir (60s / 3600s / 86400s) |
| **IP adresi (Turnstile)**     | Bot doğrulaması için Cloudflare Turnstile siteverify API'sine gönderilir | Yalnızca doğrulama için kullanılır, Worker tarafından saklanmaz                               |
| **Turnstile tokeni**          | Bot koruması için tarayıcı tarafından üretilen challenge tokeni          | Sunucu tarafında doğrulanır, doğrulama sonrası atılır                                         |

## Bu Sistemin Yapmadıkları

- **Konuşmaların kalıcı saklanması yoktur.** Sohbet mesajları bellekte işlenir ve herhangi bir veritabanına veya günlük dosyasına yazılmaz.
- **Kullanıcı hesabı veya kimlik doğrulaması yoktur.** Playground, kayıt olmadan herkese açıktır.
- **Analitik veya telemetri yoktur.** Streamlit'in yerleşik kullanım istatistikleri açıkça devre dışı bırakılmıştır (`gatherUsageStats = false`).
- **İzleme çerezleri veya parmak izi takibi yoktur.** Üçüncü taraf izleme betikleri yüklenmez.
- **IP adresi günlüğü yoktur.** IP adresleri yalnızca hız sınırlama (geçici, otomatik sona eren) ve Turnstile doğrulaması (anlık) için kullanılır.
- **Veri paylaşımı yoktur.** Verileriniz, yukarıda listelenen Cloudflare hizmetleri dışında hiçbir tarafla paylaşılmaz.

## Cloudflare Turnstile

Playground, bot koruması için Cloudflare Turnstile'ı görünmez (invisible) modda kullanmaktadır. Turnstile:

- Çoğu durumda kullanıcı etkileşimi gerektirmeden arka planda sessizce çalışır
- Cloudflare'in siteverify API'sine karşı sunucu tarafında doğrulanan bir challenge tokeni üretir
- Doğrulama kapsamında istemci IP adresini Cloudflare'e gönderir
- İzleme çerezi kullanmaz — yalnızca challenge için gerekli işlevsel çerezleri kullanır

Daha fazla bilgi için: [Cloudflare Turnstile Gizlilik](https://www.cloudflare.com/privacypolicy/)

## Hız Sınırlama

Hız sınırları, otomatik sona erme ile Cloudflare KV kullanılarak IP adresi başına uygulanmaktadır:

| Pencere | Limit | TTL |
|---------|-------|-----|
| Dakika | 5 | 60 saniye |
| Saat | 30 | 3600 saniye |
| Gün | 100 | 86400 saniye |

Hız sınırlama sayaçları, Worker tarafından saklanan **tek** veridir. Otomatik olarak sona erer ve bireyleri tanımlamak için kullanılamaz.

## Açık Kaynak ve Şeffaflık

Bu tamamen açık kaynaklı bir projedir. Worker API, Streamlit playground, corpus builder pipeline ve tüm CI/CD workflow'ları dahil olmak üzere kod tabanının tamamı bu repository'de herkese açık ve denetlenebilir durumdadır.

- **Her kod değişikliği izlenebilir.** Tüm güncellemeler herkese açık repository'ye commit edilir.
- **Gizli dağıtım yoktur.** Üretim ortamı, GitHub'da inceleyebildiğiniz kaynak kodun aynısından derlenir ve dağıtılır.
- **Denetlenebilir pipeline'lar.** Workflow yapılandırmaları, Dockerfile'lar ve dağıtım betikleri herkese açık repository'nin bir parçasıdır.

## Üçüncü Taraf Hizmetler

| Sağlayıcı | Hizmet | İşlenen Veri | Gizlilik Politikası |
|------------|--------|-------------|---------------------|
| Cloudflare | Workers, Containers, AI Search, Workers AI, KV, R2 | Sohbet mesajları (bellekte), IP (hız sınırlama), Turnstile tokenleri | [cloudflare.com/privacypolicy](https://www.cloudflare.com/privacypolicy/) |
| Cloudflare | Turnstile | IP adresi, tarayıcı challenge verisi | [cloudflare.com/privacypolicy](https://www.cloudflare.com/privacypolicy/) |

## Bu Bildirimde Yapılacak Değişiklikler

Bu gizlilik bildirimi, proje geliştikçe güncellenebilir. Değişiklikler, güncellenmiş tarih ile bu dosyaya yansıtılır. Proje açık kaynaklı olduğundan, değişikliklerin tüm geçmişini Git üzerinden inceleyebilirsiniz.

## İletişim

Bu gizlilik bildirimi veya EU AI Act RAG Playground hakkında sorularınız için:

**Rıza Emre ARAS** — [r.emrearas@proton.me](mailto:r.emrearas@proton.me)

**Artek İnovasyon Arge Sanayi ve Ticaret Ltd. Şti.** — [info@artek.tc](mailto:info@artek.tc)
