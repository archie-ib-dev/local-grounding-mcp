# Third-Party Notices

Local Grounding MCP interoperates with or depends on third-party software and model weights. Those components are not relicensed under this project's `AGPL-3.0-only` license. They retain their own licenses and terms.

This repository does not bundle UGround or Qwen2-VL model weights.

## UGround project source code

- Project: UGround
- Publisher: OSU NLP Group / OSU Natural Language Processing
- Source: https://github.com/OSU-NLP-Group/UGround
- License indicated by publisher: MIT License
- Bundled here: No UGround repository source code is intentionally bundled
- Relationship: External project and inference reference

## UGround-V1-2B model weights

- Model: osunlp/UGround-V1-2B
- Source: https://huggingface.co/osunlp/UGround-V1-2B
- License indicated by publisher: Apache License 2.0
- Bundled here: No
- Relationship: Separately downloaded visual-grounding model loaded from a user-specified path

Users are responsible for obtaining the weights separately and reviewing the publisher's current model card, license, acceptable-use terms, and linked notices.

## Qwen2-VL

- Project/model family: Qwen2-VL
- Publisher: Qwen Team / Alibaba Cloud
- Source: https://huggingface.co/Qwen/Qwen2-VL-2B
- License indicated for Qwen2-VL-2B: Apache License 2.0
- Bundled here: No model weights or upstream source code are intentionally bundled
- Relationship: Base architecture associated with UGround-V1-2B

## Model Context Protocol Python SDK

- Package: `mcp`
- Source: https://github.com/modelcontextprotocol/python-sdk
- License indicated by publisher: MIT License
- Bundled here: Installed as a dependency; source is not intentionally vendored

## PyTorch and Torchvision

- Packages: `torch`, `torchvision`
- Sources: https://github.com/pytorch/pytorch and https://github.com/pytorch/vision
- License indicated by publishers: BSD-style licenses; review each installed distribution
- Bundled here: Installed as dependencies; source and binary distributions are not intentionally vendored

## Hugging Face Transformers

- Package: `transformers`
- Source: https://github.com/huggingface/transformers
- License indicated by publisher: Apache License 2.0
- Bundled here: Installed as a dependency; source is not intentionally vendored

## qwen-vl-utils

- Package: `qwen-vl-utils`
- Source: https://pypi.org/project/qwen-vl-utils/
- License indicated for the tested release series: Apache License 2.0
- Bundled here: Installed as a dependency; source is not intentionally vendored

## Pillow

- Package: `Pillow` / `PIL`
- Source: https://github.com/python-pillow/Pillow
- License indicated by publisher: HPND License
- Bundled here: Installed as a dependency; source is not intentionally vendored

## Dependency distributions

The installer resolves additional dependency distributions. Each may include separate notices. Users and redistributors should inspect the exact versions and license metadata in their environment.

If future releases distribute standalone binaries, containers, bundled Python environments, model weights, or hardware appliances, that release process must reproduce all notices required by bundled third-party components.

Third-party names, marks, and copyrights belong to their owners. Inclusion does not imply endorsement. This notice is informational and not legal advice. Please report incomplete or incorrect attribution with authoritative source information.
