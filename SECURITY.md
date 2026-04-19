# Security Policy

## Supported Scope

This repository focuses on secure defaults for API usage, deployment, and secret handling.

## Reporting a Vulnerability

- Do not open public issues for active security vulnerabilities.
- Report privately to the repository maintainers.
- Include reproduction steps, impact, and affected files/endpoints.

## Secure Configuration Checklist

- Keep `.env` out of version control.
- Use a valid `TAVILY_API_KEY` only in deployment environments.
- Set `CORS_ALLOW_ORIGINS` to explicit frontend origins in production.
- Rotate API keys immediately if exposed.
- Keep container base image tags pinned and periodically refreshed.

## Operational Practices

- Run tests before every release: `pytest -q`
- Review dependency updates routinely.
- Prefer least-privilege deployment credentials.
