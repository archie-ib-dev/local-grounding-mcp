# Local Grounding MCP

**Privacy-first visual grounding fallback with local inference and DOM-visual hybrid routing for MCP browser agents.**

> Experimental. Initially tested on macOS Apple Silicon with Python 3.11, Apple MPS, and UGround-V1-2B.

## Why

Browser agents work best when structured page information is available:

```text
DOM / accessibility first
          |
          | no reliable element reference
          v
Local visual grounding fallback
```

Local Grounding MCP adds a private visual fallback for canvas interfaces, unlabeled controls, image-based elements, and other UI targets that are not reliably exposed through the DOM or accessibility tree.

## Architecture

```text
Claude Desktop adapter -----\
                             > Shared localhost service -> one local model
Antigravity adapter --------/
```

The shared service provides:

- one model process across multiple MCP clients;
- lazy model loading;
- serialized inference queue;
- automatic startup;
- idle shutdown;
- screenshot deletion after tensor creation;
- local token and latency metrics;
- localhost-only networking.

## Security model

The service listens on `127.0.0.1:8765` and must not listen on `0.0.0.0`.

Screenshots may temporarily exist on disk, but are deleted after visual tensors are created when `delete_after_read=true`.

Do not commit browser tokens, credentials, screenshots, local MCP configuration files, logs, metrics, or model weights.

## Status

This repository is under active development. Installation scripts, automated tests, model setup documentation, and complete third-party notices will be added before the first public release.
