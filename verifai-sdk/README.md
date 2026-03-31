# VerifAI SDK

Python SDK for VerifAI - AI Quality Review.

## Features

- Single and batch review of AI-generated content
- Multi-agent review with specialized agents
- Cost tracking and ROI calculation
- Compliance checks (GDPR, HIPAA, etc.)
- Async support
- CLI tools

## Installation

```bash
cd verifai-sdk
pip install -e .
```

## Quick Start

```python
from verifai_sdk import VerifAIClient

client = VerifAIClient(api_key="your-api-key")
result = client.review("Your AI-generated text")
print(result.score)
client.close()
```

## CLI

```bash
verifai review "The iPhone 15 has 8K video" --rubric factuality
verifai improve "This is the best product ever!" --iterations 3
verifai compliance "We collect user data" --framework gdpr
verifai multi-agent "Sensitive content" --agents safety,factuality,brand
verifai cost --days 30
verifai roi --daily-volume 5000 --cost-per-review 0.05
verifai batch reviews.txt --output results.json
```

## Examples

```bash
python examples/basic_usage.py
python examples/async_usage.py
```

## Testing

```bash
pytest tests/ -v
```

## Configuration

Environment variables:

- VERIFAI_API_KEY
- VERIFAI_BASE_URL
- VERIFAI_TIMEOUT
- VERIFAI_MAX_RETRIES
- VERIFAI_RETRY_BACKOFF
- VERIFAI_CACHE_ENABLED
- VERIFAI_CACHE_TTL
- VERIFAI_LOG_LEVEL
