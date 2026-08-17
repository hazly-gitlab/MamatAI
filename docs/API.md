# API Specification

All endpoints are versioned under `/api/v1/`:
- `POST /auth/register` & `POST /auth/login`
- `GET /conversations` & `POST /conversations`
- `POST /conversations/{id}/messages/stream` (SSE)
- `POST /documents/upload` & `GET /documents`
- `POST /vision/analyse`
- `POST /voice/stt` & `POST /voice/tts`
