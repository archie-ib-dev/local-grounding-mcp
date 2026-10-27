# Security Policy

## Supported status

This project is experimental and has initially been tested on macOS Apple Silicon.

## Security boundary

The shared service must bind only to `127.0.0.1`.

Never commit or publish:

- API keys or browser-extension tokens;
- passwords, cookies, or private keys;
- screenshots or private page contents;
- local MCP configuration files;
- runtime logs or metrics;
- model weights.

## Vulnerability reporting

Do not disclose security vulnerabilities through public issues.

Until a dedicated security contact is published, contact the maintainer privately through the GitHub profile contact method.
