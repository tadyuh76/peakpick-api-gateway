# PeakPick API Gateway

Single REST entry point for the PeakPick frontend. It proxies requests to backend services and applies role/store authorization.

Run locally:

```bash
pip install -r requirements.txt
uvicorn services.api_gateway.main:app --reload --port 8000
```
