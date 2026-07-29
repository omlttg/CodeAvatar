# CodeAvatar Context

## Environment
- Workspace: `/home/thienvu/workspace/CodeAvatar`
- OS: Linux
- Python: system installation (requires uv/pip environment verification)
- Backend: FastAPI, SQLite (WAL mode)
- Frontend: React + Vite
- Portability binary: `bin/bin/gh` available in project root

## Workspace Assets
- `AGENT.md`: AI rules and code standards
- `ARCHITECTURE.md`: Architecture vision, pipeline details, schemas, and integration points
- `HANDOFF.md`: Read-me handoff from the previous human/agent step

## Key Constraints
- Language preference: Vietnamese for communication, English for Markdown headings
- Bilingual comments in Vietnamese and English for code files
- GPU VRAM management: sequentially offload models (`torch.cuda.empty_cache()`), run heavy parts in isolated child subprocesses
- Secure paths: prevent path traversal vulnerabilities
