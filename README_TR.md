# EU AI Act RAG

**[Canlı Demo](https://eu-ai-act-rag-playground.aras.tc/)**

## Pipeline

```mermaid
flowchart TD
    CLI["run.py --workflow workflows/eu-ai-act.yaml"]
    CONFIG["src/config.py<br/>load_config → PipelineConfig"]
    PIPELINE["src/pipeline.py<br/>run_pipeline"]

    CLI -->|"YAML parse"| CONFIG
    CONFIG -->|"PipelineConfig"| PIPELINE

    subgraph PHASE_1 ["Phase 1 — SPARQL"]
        S_LOOP["For each step in<br/>config.sparql.steps"]
        S_RENDER["src/sparql/queries.py<br/>render_step"]
        S_QUERY["src/sparql/client.py<br/>execute_query"]
        S_SCRIPT["src/sparql/processor.py<br/>execute_script"]
        S_CTX["context[step.name] = output"]

        S_LOOP --> S_RENDER
        S_RENDER -->|"SPARQL query string"| S_QUERY
        S_QUERY -->|"list&lt;Binding&gt;"| S_SCRIPT
        S_SCRIPT -->|"output"| S_CTX
        S_CTX -->|"next step"| S_LOOP
    end

    subgraph PHASE_2 ["Phase 2 — Fetch"]
        F_URI["select_uri<br/>uri_select_script from YAML"]
        F_DL["_download<br/>GET + Accept: application/zip"]
        F_ZIP["_extract_zip<br/>ZIP → *.fmx.xml to tmpdir"]

        F_URI -->|"manifestation URL"| F_DL
        F_DL -->|"bytes"| F_ZIP
    end

    subgraph PHASE_3 ["Phase 3 — Parse"]
        P_ACT["*.000101.fmx.xml<br/>Main ACT file"]
        P_ART["parse_articles<br/>DIVISION → ARTICLE → PARAG"]
        P_REC["parse_recitals<br/>PREAMBLE → CONSID → NP"]
        P_ANX["parse_annex<br/>*.01XXXX.fmx.xml × 13"]
        P_DOC["ParsedDocument<br/>articles + recitals + annexes"]

        P_ACT --> P_ART
        P_ACT --> P_REC
        P_ANX --> P_DOC
        P_ART --> P_DOC
        P_REC --> P_DOC
    end

    subgraph PHASE_4 ["Phase 4 — Convert + Postprocess"]
        C_FM["_build_frontmatter<br/>YAML frontmatter from templates"]
        C_BODY["_article_to_markdown<br/>Structured body text"]
        C_NORM["_normalize<br/>NBSP, ZWSP, BOM cleanup"]
        C_WRITE["write_text<br/>corpus/**/*.md"]

        C_FM --> C_NORM
        C_BODY --> C_NORM
        C_NORM --> C_WRITE
    end

    subgraph PHASE_V ["Phase 3.5 — Validate (advisory)"]
        V_SRC["_build_source_text_map<br/>XML yeniden parse → ham metin"]
        V_DET["_run_deterministic<br/>sayı · boş · numaralandırma · yapı"]
        V_COV["coverage ratio<br/>parsed_len / source_len"]
        V_RPT["validation-report.json"]

        V_SRC --> V_DET --> V_COV --> V_RPT
    end

    PIPELINE --> PHASE_1
    PHASE_1 -->|"context dict"| PHASE_2
    PHASE_2 -->|"tmpdir: Path"| PHASE_3
    PHASE_3 -->|"ParsedDocument"| PHASE_V
    PHASE_V -->|"her zaman devam eder"| PHASE_4

    PHASE_4 -->|"PipelineSummary"| SUMMARY["Pipeline Summary<br/>sparql: 4 ok | fetch: 1 ok | validation: 3 ok<br/>articles: 113 | recitals: 180 | annexes: 13"]

    style PHASE_1 fill:#1a1a2e,stroke:#e94560,color:#fff
    style PHASE_2 fill:#1a1a2e,stroke:#0f3460,color:#fff
    style PHASE_3 fill:#1a1a2e,stroke:#16213e,color:#fff
    style PHASE_V fill:#1a1a2e,stroke:#c0392b,color:#fff
    style PHASE_4 fill:#1a1a2e,stroke:#1a8a42,color:#fff
```

## Hızlı Başlangıç

```bash
pip install -r workflow-engine/requirements.txt
python run.py --workflow workflows/eu-ai-act.yaml
```

## Çıktı

```
dist/eu-ai-act-{zaman_damgası}/
├── validation-report.json
└── corpus/
    ├── articles/*.md          (113)
    ├── recitals/*.md          (180)
    └── annexes/*.md           (13)
```

## Doğrulama (Validation)

Pipeline, parse ve convert aşamaları arasında deterministik bir doğrulama adımı (Phase 3.5) çalıştırır. **Advisory modda** çalışır — uyarı loglar ve rapor üretir ancak pipeline'ı asla durdurmaz.

Her öğe için iki bağımsız metin çıkarma yolu karşılaştırılır:

| Yol                        | Yöntem                          | Kapsam                         |
|----------------------------|---------------------------------|--------------------------------|
| **Kaynak** (validator)     | `etree.tostring(method="text")` | Tüm metin düğümleri — kapsamlı |
| **Ayrıştırılmış** (parser) | Seçici tag traversal            | Yalnızca tanınan elementler    |

Parser'ın yapısal taraması bir alt ağacı atlarsa, kapsamlı kaynak yolu bunu **kapsama oranı** (`parsed_len / source_len`) aracılığıyla yakalar.

**Kontroller:**

| Kontrol               | Tür                                  | Eşik                 |
|-----------------------|--------------------------------------|----------------------|
| Sayı doğrulama        | madde=113, gerekçe=180, ek=13        | tam eşleşme          |
| Boş içerik            | gövdesi olmayan öğeler               | herhangi biri = fail |
| Sıralı numaralandırma | madde numaralarında boşluk           | herhangi biri = warn |
| Yapısal bütünlük      | eksik başlık veya bölüm bağlamı      | herhangi biri = warn |
| Kapsama oranı         | öğe başına `parsed_len / source_len` | < 0.8 = warn         |

Yapılandırma `workflows/eu-ai-act.yaml` dosyasındaki `validation:` bölümünde bulunur.

## RAG Yapılandırması

| Parametre        | Değer                                      |
|------------------|--------------------------------------------|
| Embedding Model  | `@cf/qwen/qwen3-embedding-0.6b`            |
| Generation Model | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` |
| Chunk Boyutu     | 384 token                                  |
| Chunk Örtüşme    | %20                                        |
| Vektör Deposu    | Cloudflare Vectorize (1024 boyut)          |
| Nesne Deposu     | Cloudflare R2                              |

### Cloudflare Belgeleri

- [AI Search](https://developers.cloudflare.com/ai-search/)
- [Vectorize](https://developers.cloudflare.com/vectorize/)
- [R2 Object Storage](https://developers.cloudflare.com/r2/)

## Proje Yapısı

```
eu-ai-act-rag/
├── run.py                          # Giriş noktası
├── workflows/
│   └── eu-ai-act.yaml             # Workflow tanımı
├── workflow-engine/
│   ├── requirements.in
│   ├── requirements.txt
│   └── src/
│       ├── config.py
│       ├── converter.py
│       ├── fetcher.py
│       ├── logger.py
│       ├── parser.py
│       ├── pipeline.py
│       ├── result.py
│       ├── validator.py
│       └── sparql/
│           ├── client.py
│           ├── processor.py
│           └── queries.py
├── worker/                         # Cloudflare Worker (AutoRAG API)
│   ├── wrangler.jsonc
│   ├── package.json
│   └── src/
│       ├── index.ts
│       ├── config.ts
│       ├── types.ts
│       ├── translations.ts
│       ├── ai/
│       │   ├── manager.ts
│       │   └── prompts/
│       │       └── system-prompt.md
│       ├── middleware/
│       │   └── ratelimit.ts
│       ├── validation/
│       │   ├── request.ts
│       │   └── schema.ts
│       └── utils/
│           ├── errors.ts
│           └── logging.ts
├── playground/                     # Streamlit - Cloudflare Containers
│   ├── wrangler.jsonc
│   ├── package.json
│   ├── Dockerfile
│   ├── start.sh
│   ├── src/
│   │   └── index.ts               # Hono reverse proxy
│   └── app/
│       ├── app.py
│       ├── translations.py
│       ├── export_utils.py
│       ├── locales/
│       │   ├── en.json
│       │   └── tr.json
│       └── .streamlit/
│           └── config.toml
└── dist/                           # Çıktı (gitignore)
```

## CI/CD

| Workflow                  | Tetikleyici                            | Runner        | Çıktı                  |
|---------------------------|----------------------------------------|---------------|------------------------|
| `build-corpus.yml`        | `workflows/**` push/PR, manuel         | ubuntu-latest | corpus artifact        |
| `build-gdpr-corpus.yml`   | `workflows/**` push, manuel            | ubuntu-latest | gdpr-corpus artifact   |
| `deploy-r2.yml`           | manuel                                 | self-hosted   | R2 bucket yüklemesi    |
| `deploy-worker.yml`       | `worker/**` push, manuel               | self-hosted   | Cloudflare Worker      |
| `deploy-playground.yml`   | `playground/**` push, manuel           | self-hosted   | Cloudflare Container   |
| `release-corpus.yml`      | manuel (version input)                 | ubuntu-latest | GitHub Release v-x.y.z |

## Lisans

MIT Lisansı — Telif Hakkı (C) 2026 Rıza Emre ARAS, Artek İnovasyon Arge Sanayi ve Ticaret Ltd. Şti.

Ayrıntılar için [LICENSE](LICENSE) ve [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES) dosyalarına bakınız.
