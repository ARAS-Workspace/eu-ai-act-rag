# EU AI Act RAG Worker — API Referansı

## Endpoint

```
POST /api/v1/chat/completions
```

## İstek

```json
{
  "messages": [
    { "role": "user", "content": "AB Yapay Zekâ Yasası'nda tanımlanan risk kategorileri nelerdir?" },
    { "role": "assistant", "content": "AB Yapay Zekâ Yasası dört risk kategorisi tanımlar: kabul edilemez, yüksek, sınırlı ve minimal risk." },
    { "role": "user", "content": "Hangi yapay zekâ sistemleri yüksek riskli kategorisine girer?" }
  ],
  "locale": "tr"
}
```

| Alan            | Tip     | Zorunlu | Açıklama                                                                                         |
|-----------------|---------|---------|--------------------------------------------------------------------------------------------------|
| `messages`      | array   | evet    | Konuşma geçmişi. Her mesajda `role` (`"user"` veya `"assistant"`) ve `content` (string) bulunur. |
| `locale`        | string  | hayır   | Yanıt dili: `"en"` (varsayılan) veya `"tr"`.                                                     |
| `stream`        | boolean | hayır   | İleride kullanım için ayrılmıştır.                                                               |
| `searchOptions` | object  | hayır   | Varsayılan AI Search parametrelerini geçersiz kılar. Aşağıya bakınız.                            |

### searchOptions

```json
{
  "messages": [
    { "role": "user", "content": "Yüksek riskli yapay zekâ sağlayıcılarının yükümlülükleri nelerdir?" }
  ],
  "searchOptions": {
    "model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "rewriteQuery": true,
    "reRanking": true,
    "maxResults": 10,
    "scoreThreshold": 0.5
  }
}
```

| Alan             | Tip     | Varsayılan                                   | Açıklama                              |
|------------------|---------|----------------------------------------------|---------------------------------------|
| `model`          | string  | `@cf/meta/llama-3.3-70b-instruct-fp8-fast`   | Üretim modeli.                        |
| `rewriteQuery`   | boolean | `true`                                        | Daha iyi arama için sorgu yeniden yazımı. |
| `reRanking`      | boolean | `true`                                        | Sonuçların semantik yeniden sıralaması. |
| `maxResults`     | integer | `20`                                          | Maksimum alınan parça sayısı (1–50).  |
| `scoreThreshold` | number  | `0.4`                                         | Minimum ilgililik puanı (0–1).        |

**İzin verilen modeller:**

- `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- `@cf/meta/llama-3.1-8b-instruct`
- `@cf/meta/llama-3.1-70b-instruct`
- `@cf/mistral/mistral-7b-instruct-v0.1`
- `@cf/google/gemma-7b-it`
- `@cf/qwen/qwen1.5-7b-chat-awq`

## Yanıt

### 200 OK

```json
{
  "response": "AB Yapay Zekâ Yasası kapsamında yüksek riskli yapay zekâ sistemleri arasında kritik altyapılarda (örneğin ulaşım, enerji), eğitim ve mesleki öğretimde (örneğin sınav puanlama), istihdam ve işçi yönetiminde (örneğin CV tarama), temel özel ve kamu hizmetlerinde (örneğin kredi puanlama), kolluk kuvvetleri, göç ve sınır kontrolü ile yargı yönetiminde kullanılanlar yer almaktadır. Bu sistemlerin AB pazarına sunulmadan önce risk yönetimi, veri yönetişimi, teknik dokümantasyon, şeffaflık, insan gözetimi ve sağlamlık gibi katı gereksinimlere uymaları gerekmektedir.",
  "sources": [
    { "filename": "eu-ai-act-final-text/article-6.md", "score": 0.82, "content": "## Article 6 — Classification rules for high-risk AI systems\n\n1. Irrespective of whether an AI system is placed on the market..." },
    { "filename": "eu-ai-act-final-text/annex-III.md", "score": 0.76, "content": "## Annex III — High-risk AI systems referred to in Article 6(2)\n\n1. Biometrics, insofar as their use is permitted..." },
    { "filename": "eu-ai-act-final-text/article-9.md", "score": 0.61, "content": "## Article 9 — Risk management system\n\n1. A risk management system shall be established, implemented, documented..." }
  ],
  "metadata": {
    "search_query": "yüksek riskli yapay zekâ sistemleri kategorileri AB Yapay Zekâ Yasası",
    "duration_ms": 1842,
    "timestamp": 1740500000000
  }
}
```

| Alan                    | Tip    | Açıklama                                                                                          |
|-------------------------|--------|---------------------------------------------------------------------------------------------------|
| `response`              | string | Algılanan AB Yapay Zeka Yasası kaynaklarına dayanan, Generation model tarafından üretilmiş yanıt. |
| `sources`               | array  | Eşleşen doküman parçaları. Her öğe `filename`, `score` ve `content` içerir.                       |
| `sources[].filename`    | string | Eşleşen dokümanın R2 nesne anahtarı.                                                              |
| `sources[].score`       | number | İlgililik puanı (0–1).                                                                            |
| `sources[].content`     | string | Üretim için kullanılan alıntılanan parça metni.                                                   |
| `metadata.search_query` | string | Vektör arama için yeniden yazılan sorgu.                                                          |
| `metadata.duration_ms`  | number | Uçtan uca işleme süresi (milisaniye).                                                             |
| `metadata.timestamp`    | number | Yanıtın üretildiği Unix epoch zamanı (ms).                                                        |

### 400 Bad Request

```json
{
  "error": {
    "type": "invalid_request",
    "message": "Doğrulama başarısız: messages[0].content: Mesaj içeriği boş olmamalıdır"
  },
  "status": 400
}
```

### 429 Too Many Requests

```json
{
  "error": {
    "type": "rate_limit_exceeded",
    "message": "İstek limiti aşıldı. Lütfen daha sonra tekrar deneyin."
  },
  "status": 429,
  "retryAfter": 60
}
```

### 502 Bad Gateway

```json
{
  "error": {
    "type": "bad_gateway",
    "message": "Yapay zekâ servisi hatası: upstream zaman aşımı"
  },
  "status": 502
}
```

## cURL

```bash
curl -X POST https://<worker-domain>/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      { "role": "user", "content": "Yüksek riskli yapay zekâ sağlayıcılarının yükümlülükleri nelerdir?" }
    ],
    "locale": "tr"
  }'
```

## Limitler

### Doğrulama

| Kısıt                       | Değer      |
|-----------------------------|------------|
| İstek başına maksimum mesaj | 20         |
| Maksimum mesaj uzunluğu     | 4096 karakter |
| Maksimum istek gövdesi      | 20 KB      |

### Hız Sınırı (IP başına)

| Pencere | Limit |
|---------|-------|
| Dakika  | 10    |
| Saat    | 100   |
| Gün     | 500   |
