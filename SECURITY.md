# Security Policy

## Supported versions

This project currently supports the latest `main` branch.

## Reporting a vulnerability

Please do **not** open public GitHub issues for suspected vulnerabilities.

Instead, report privately to the maintainer with:

- A clear description of the issue
- Reproduction steps or proof of concept
- Potential impact
- Any suggested mitigation

If no private contact method is available yet, open a minimal issue requesting
a private channel and avoid posting exploit details.

## Security expectations for contributors

- Never commit `.env`, `.env.local`, credentials, tokens, or private keys.
- Keep `IMESSAGE_DRY_RUN=true` while testing unless explicitly validating live sends.
- Clearly label mock paths with `[MOCK]` to avoid confusion with production behavior.
- Prefer least-privilege defaults and avoid broad network/data exposure.
