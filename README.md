# Local Grounding MCP

**Privacy-first visual grounding fallback with local inference and DOM-visual hybrid routing for MCP browser agents.**

> Experimental. Currently tested on macOS Apple Silicon with Python 3.11, Apple MPS, and UGround-V1-2B.

## Why

Browser agents should use reliable DOM and accessibility references whenever possible. When structured references are unavailable or unreliable, Local Grounding MCP provides a local visual fallback for canvas interfaces, unlabeled controls, image-based elements, and other difficult UI targets.

```text
DOM / accessibility first
          |
          | no reliable structured reference
          v
Local visual grounding fallback
```

## Architecture

```text
MCP client A adapter ----\
                          > Shared localhost service -> one local model
MCP client B adapter ----/
```

The shared service provides:

- one model process shared across MCP clients;
- lazy model loading on the first model request;
- serialized model loading and inference;
- automatic service startup;
- configurable idle shutdown;
- screenshot deletion after visual tensors are created;
- local token and latency metrics;
- localhost-only networking by default.

## Current platform support

Tested:

- macOS on Apple Silicon;
- Python 3.11;
- Apple MPS;
- UGround-V1-2B;
- Claude Desktop and Antigravity as MCP clients.

Not yet tested: Intel Mac, Linux/CUDA, Windows, CPU-only inference, and other grounding models.

## Requirements

- macOS on Apple Silicon;
- Python 3.11 available as `python3.11`;
- Git;
- sufficient local storage and unified memory;
- UGround-V1-2B model weights downloaded separately.

Model weights are not included. Obtain UGround-V1-2B from its publisher and review its current terms:

```text
https://huggingface.co/osunlp/UGround-V1-2B
```

Default location:

```text
~/Models/UGround-V1-2B
```

Alternative location:

```bash
export GROUNDING_MODEL_PATH="/absolute/path/to/UGround-V1-2B"
```

## Installation

```bash
git clone https://github.com/archie-ib-dev/local-grounding-mcp.git
cd local-grounding-mcp
./scripts/install.sh
```

The installer creates an isolated environment at `~/.local/share/local-grounding-mcp/venv` and command links under `~/.local/bin`. Add `~/.local/bin` to `PATH` if necessary.

Verify:

```bash
local-grounding-doctor
```

## MCP configuration

The installer automatically runs:

```bash
local-grounding-config
```

It creates ready-to-paste snippets at:

```text
~/.config/local-grounding-mcp/claude-desktop.json
~/.config/local-grounding-mcp/antigravity.json
```

The snippets use absolute paths and do not overwrite existing client configuration. Merge only the generated `local-grounding` entry into the existing `mcpServers` object. Static examples are also available in `examples/`.

## Commands

```bash
local-grounding-doctor
local-grounding-status
local-grounding-stop
local-grounding-metrics
local-grounding-config
```

Lower-level commands:

```bash
local-grounding-mcp
local-grounding-service
```

An MCP adapter normally starts the service automatically. Status checks do not intentionally load the model. Stopping the process releases the model with that process.

## MCP tools

- `grounding_health`: return status without intentionally loading the model;
- `load_grounding_model`: explicitly load the shared model;
- `locate_target`: locate a described target in a screenshot;
- `cleanup_grounding_screenshots`: remove orphan screenshots by age.

Visual grounding is a fallback. Clients should inspect DOM and accessibility information first.

## Configuration

Common environment variables:

```text
GROUNDING_CLIENT
GROUNDING_HOST
GROUNDING_PORT
GROUNDING_IDLE_SECONDS
GROUNDING_MODEL_PATH
GROUNDING_SCREENSHOT_DIR
GROUNDING_CACHE_DIR
GROUNDING_LOG_DIR
GROUNDING_SERVICE_SCRIPT
GROUNDING_SERVICE_LOG
GROUNDING_START_LOCK
GROUNDING_CONFIG_DIR
```

The default host is `127.0.0.1`. Do not expose the service on `0.0.0.0` without authentication and authorization.

## Privacy and telemetry

Inference is local. Screenshots may briefly exist on disk. With `delete_after_read=true`, the consumed screenshot is deleted after processing inputs are created and before inference completes.

Metrics may include timestamps, operation names, client labels, process IDs, image dimensions, token counts, timings, deletion status, and success status. The current metrics design is not intended to store screenshot contents, page text, URLs, cookies, credentials, browser-extension tokens, or target descriptions. Review logs and metrics before sharing.

## Baseline measurement

One validated clean-environment run on Apple Silicon, MPS, and FP32 produced:

```text
Image size:              753 x 620
Visual tokens:           1,044
Input tokens:            1,121
Generated tokens:        11
Model load:              5.304 seconds
Preprocessing:           0.026 seconds
Inference:               8.347 seconds
Cold-start total:        13.685 seconds
Screenshot deleted:      true
```

Results vary with hardware, dependencies, image dimensions, model state, and workload.

## Uninstall

```bash
./scripts/uninstall.sh
```

The uninstaller removes the environment and command links. It preserves model weights, logs, metrics, generated snippets, and client configuration.

## Security

See `SECURITY.md`. Keep the service on localhost, do not commit secrets or client configuration, and review automation before allowing access to sensitive applications.

## License

Local Grounding MCP is licensed under the GNU Affero General Public License version 3 only (`AGPL-3.0-only`). Commercial use is allowed under the AGPLv3, subject to its terms.

The license is intended to keep modifications to the covered runtime available under the same open-source terms, including where AGPL network-interaction obligations apply. Organizations requiring different terms for proprietary use may contact the copyright holder to discuss alternative licensing. No alternative commercial license or commercial terms are granted through this repository.

Third-party software and separately downloaded models retain their own licenses. See `THIRD_PARTY_NOTICES.md`.

## Contributions

Issues, documentation, tests, and code contributions are welcome. Unless a separate written agreement applies, accepted contributions are expected to be provided under `AGPL-3.0-only`. A Contributor License Agreement may be required before accepting work intended for an alternatively licensed edition. See `CONTRIBUTING.md`.

## Status

Experimental and under active development. Platform support, installation behavior, security boundaries, and dependency compatibility may change before a stable release.
