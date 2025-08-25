# Software Requirements

- Python 3.12+
- Node.js 18+ with pnpm for React UI
- Windows (PowerShell) primary dev target; cross-platform backend
- OpenAI API key (environment variable)

## Functional
- Upload JPEGs and store to `jpgDownload`
- Extract JSON via LLM (Ts1) and save to `jpg2json`
- Run webbot + mapping (Ts2) and save to `json2mapping`
- Provide current automation state and aggregated logs via REST

## Non-Functional
- Structured logs with levels, codes, components
- Clear Turkish states and consistent transitions
- Simple temp file lifecycle and cleanup on new uploads
