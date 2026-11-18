# Ayo (formerly SafeLine / Leda) 🛡️✨

<p align="center">
  <img src="https://img.shields.io/badge/LangGraph-Deterministic_Agent_State_Machine-1c3c3c?logo=langchain&logoColor=white" alt="LangGraph">
  <img src="https://img.shields.io/badge/Telephony-Twilio_Media_Streams_·_Asterisk-red" alt="Telephony">
  <img src="https://img.shields.io/badge/Audio_Codec-G.711_μ--law_(8kHz)-blue" alt="G.711">
  <img src="https://img.shields.io/badge/Gemini_Live-Full--Duplex_Audio-4285f4?logo=google&logoColor=white" alt="Gemini Live">
  <img src="https://img.shields.io/badge/Photon_2.0-iMessage_Agent-34c759?logo=imessage&logoColor=white" alt="Photon">
  <img src="https://img.shields.io/badge/Python-3.12-3776ab?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Next.js-16_React_19-000000?logo=nextdotjs&logoColor=white" alt="Next.js 16">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="MIT License">
</p>

<p align="center">
  <b>The 24/7 Child-Safety Line That Actually Listens</b><br>
  Full-Duplex Voice Telephony & Photon 2.0 Silent-Text Triage Engineered with Clinical Trauma Grounding
</p>

Built for **HackPrinceton Fall '26** (Princeton University, Nov 13–15, 2026) and scaling under **Education for Equality (E4E)**.

---

## Why Ayo
- **1B+ children** experience violence annually (WHO/UNICEF); **500,000+ child helpline contacts/yr** go unanswered (Child Helpline International).
- In Nigeria, **6 in 10 children** experience violence before 18, yet **<5% receive help**—and **88% of child sexual abuse victims know their abuser**, making speaking aloud unsafe.
- **71% of US 988 crisis centers** report understaffing (*JAMA Network Open*).
- **2026 Acoustic AI Finding:** Voice models act on words, not tone (*Bartelds et al. 2026*). Ayo introduces an independent acoustic listener sidecar to capture crying, whisper mode, and tremor.

---

## 📐 Architecture & Agent Pipeline

```mermaid
flowchart TD
    subgraph INTAKE["1. Dual-Channel Intake"]
        A["Phone Caller (GSM/PSTN)"] -->|8kHz Audio| B["Twilio Media Streams / Asterisk"]
        C["Youth on iPhone"] -->|Silent iMessage| D["Photon 2.0 Spectrum Bridge"]
    end

    subgraph TELEPHONY["2. Real-Time Telephony Core"]
        B <-->|WebSocket| E["G.711 μ-law Codec & 3:1 Integer Decimator"]
        E <-->|Bidirectional Audio| F["Gemini Live (gemini-3.1-flash)"]
    end

    subgraph AGENT["3. LangGraph Triage State Machine"]
        F -.->|Transcript| G["Node 1: Deterministic PII Scrubber"]
        D -->|Text| G
        G --> H["Node 2: Severity & Harm Evaluator (Deterministic Floor + Flash)"]
        H --> I["Node 3: Trauma Responder (NICHD Protocol & De-blaming)"]
        I --> J["Node 4: Case Store & Caseworker Dispatch"]
    end

    subgraph DISPATCH["4. Sovereign Action & Forensics"]
        J --> K["Automated Caseworker Emergency Voice Call"]
        J --> L["SHA-256 Tamper-Evident Forensic Ledger"]
        J --> M["Next.js Command Center (Hotspot Map & Audio Trace)"]
    end
```

### Key Engineering Systems
1. **Low-Latency Audio Telephony:** Pure-Python integer 3:1 decimation filter with precomputed lookup tables converting 24 kHz Gemini Live audio into 8 kHz G.711 $\mu$-law for telephony with sub-millisecond conversion and zero external C dependencies.
2. **LangGraph Deterministic Guardrails:** 4-node state machine (`pii_scrubber.py` $\rightarrow$ trauma-informed minimal-questioning intake $\rightarrow$ Risk 0–3 evaluation with deterministic fallback floors $\rightarrow$ emergency caseworker dispatch).
3. **Voice Biometrics:** ReDimNet2+ speaker recognition models over 8 kHz phone channels, enabling zero-credential caller re-identification across anonymous and burner numbers.
4. **Caseworker Command Center (`/console`):** Live intake simulator, PII-scrubbed transcript stream, dual-region geographic hotspot map (Nigeria + US), Arlequin cross-case entity forensics, and 40-case synthetic eval runner.

---

## 🔬 Benchmark & Synthetic Evaluation Suite

Before deployment, we engineered an automated **40-case synthetic evaluation suite** spanning Nigerian Pidgin, British/West African English, and US urban vernacular:

| Metric | Result | Target Benchmark | Status |
|---|:---:|:---:|:---:|
| **Escalation Recall on Crisis** | **100.0%** | >99.0% | ✅ Passed (40/40 cases correctly flagged) |
| **False Positive Rate** | **0.0%** | <2.0% | ✅ Passed (Normal non-crisis inquiries never falsely escalated) |
| **PII Redaction Leaks** | **0 tokens** | 0 tokens | ✅ Passed (Full regex strip of phone, name, address) |
| **Guardrail Execution Latency** | **0.052 ms** | <5.0 ms | ✅ Passed (Sub-millisecond memory execution) |

---

## 🚀 Run Locally

```bash
# Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Automated Evals
python eval/test_ayo_prompt.py
python eval/test_gemini_live.py

# Frontend
cd frontend
npm run dev
# Public Product Site: http://localhost:3000
# Caseworker Console:  http://localhost:3000/console
```

---

## 🔒 Private Production Repositories & Access

Ayo was developed as the child-safety sister platform to **Sabi** (Education for Equality). 

For hiring managers, researchers, or partner organizations wishing to inspect the production Asterisk telephony server, SIP configurations, or live African telco trunking, please request read access via **`nivie@wesleyan.edu`**.
