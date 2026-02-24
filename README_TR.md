# EU AI Act RAG

## Pipeline

```mermaid
flowchart TD
    CLI["build.py<br/><code>--output dist/corpus</code>"]
    YAML["data.yaml<br/>Workflow Definition"]
    CONFIG["src/config.py<br/>load_config → PipelineConfig"]
    PIPELINE["src/pipeline.py<br/>run_pipeline"]

    CLI -->|"Path"| CONFIG
    YAML -->|"YAML parse"| CONFIG
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

    PIPELINE --> PHASE_1
    PHASE_1 -->|"context dict"| PHASE_2
    PHASE_2 -->|"tmpdir: Path"| PHASE_3
    PHASE_3 -->|"ParsedDocument"| PHASE_4

    PHASE_4 -->|"PipelineSummary"| SUMMARY["Pipeline Summary<br/>sparql: 4 ok | fetch: 1 ok<br/>articles: 113 | recitals: 180 | annexes: 13"]

    style PHASE_1 fill:#1a1a2e,stroke:#e94560,color:#fff
    style PHASE_2 fill:#1a1a2e,stroke:#0f3460,color:#fff
    style PHASE_3 fill:#1a1a2e,stroke:#16213e,color:#fff
    style PHASE_4 fill:#1a1a2e,stroke:#1a8a42,color:#fff
```

## Hızlı Başlangıç

```bash
pip install -r workflow-engine/requirements.txt
python build.py
```

```bash
python build.py --output path/to/output
```

## Çıktı

| Bölüm    | Adet | Dizin                         |
|----------|------|-------------------------------|
| Maddeler | 113  | `dist/corpus/articles/*.md`   |
| Gerekçe  | 180  | `dist/corpus/recitals/*.md`   |
| Ekler    | 13   | `dist/corpus/annexes/*.md`    |


## Proje Yapısı


## Project Structure

```
eu-ai-act-rag/
├── build.py                    
├── data.yaml                   
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
│       └── sparql/
│           ├── client.py       
│           ├── processor.py    
│           └── queries.py      
└── dist/corpus/                
```

## Lisans

MIT Lisansı — Telif Hakkı (C) 2026 Rıza Emre ARAS

Ayrıntılar için [LICENSE](LICENSE) ve [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES) dosyalarına bakınız.