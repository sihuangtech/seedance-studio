# Seedance Studio

[中文 README](README_zh-CN.md)

Seedance Studio is a Python client project for the Volcengine Ark Seedance video generation API.

It includes:

- Streamlit GUI for creating, querying, listing, cancelling, and deleting tasks
- `SeedanceClient` wrapper backed by the official Volcengine Ark Python SDK
- Content helpers for text, images, videos, audio, and draft tasks
- CLI for quick local operations
- Unit tests that validate SDK call arguments without real API calls

## Installation

Recommended with `uv`:

```powershell
uv venv .venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements-dev.txt
```

If the default `uv` cache directory has permission issues, keep the cache inside the project:

```powershell
$env:UV_CACHE_DIR=".uv-cache"
uv venv .venv
uv pip install -r requirements-dev.txt
```

The project uses the official Ark SDK dependency: `volcengine-python-sdk[ark]`.

## Configuration

Copy `.env.example` to `.env`, or set environment variables directly:

```powershell
$env:SEEDANCE_API_KEY="your Volcengine Ark API key"
```

Optional environment variables:

- `SEEDANCE_MODEL`: default model or endpoint ID
- `SEEDANCE_MODEL_CHOICES`: comma-separated model IDs shown in the GUI model selector
- `SEEDANCE_BASE_URL`: API base URL
- `SEEDANCE_TIMEOUT`: request timeout in seconds

## GUI

```powershell
.venv\Scripts\Activate.ps1
streamlit run src/gui/app.py
```

After the app starts, open the local browser page and enter your API key, model, prompt, media inputs, and generation settings.

## CLI Examples

Text-to-video:

```powershell
.venv\Scripts\Activate.ps1
seedance create --model doubao-seedance-2-0-260128 --prompt "A kitten watches the rain by the window, cinematic, soft lighting" --ratio 16:9 --duration 5
```

Image-to-video with a first frame:

```powershell
seedance create --model doubao-seedance-2-0-260128 --prompt "The camera slowly pushes in, the character smiles" --image-url "https://example.com/first.png" --image-role first_frame
```

Query and wait until the task finishes:

```powershell
seedance wait cgt-xxxx --interval 5 --timeout 900
```

List tasks:

```powershell
seedance list --status succeeded --page-size 10
```

Cancel a queued task or delete a completed task record:

```powershell
seedance delete cgt-xxxx
```

## Python Example

This project uses a `src` layout. If you run scripts without editable installation, set:

```powershell
$env:PYTHONPATH="src"
```

```python
from core import SeedanceClient, text_content

client = SeedanceClient.from_env()

task = client.create_task(
    model="doubao-seedance-2-0-260128",
    content=[text_content("A kitten watches the rain by the window, cinematic, soft lighting")],
    ratio="16:9",
    duration=5,
    generate_audio=True,
)

result = client.wait_for_task(task["id"])
print(result["status"])
print(result.get("content", {}).get("video_url"))
```

## Project Structure

```text
src/
  core/       # SDK core: client, config, content helpers, errors
  cli/        # command-line entry point
  gui/        # Streamlit GUI modules
tests/
  test_client.py
```

## Verification

```powershell
.venv\Scripts\Activate.ps1
python -m pytest
python -m ruff check .
```

Unit tests do not call the real API by default. To run the real SDK integration test:

```powershell
$env:SEEDANCE_RUN_INTEGRATION_TESTS="1"
$env:SEEDANCE_API_KEY="your Volcengine Ark API key"
python -m pytest -m integration
```

## Notes

- Video generation tasks are asynchronous. Create a task first, then query its status.
- Generated video URLs expire. Save or transfer results promptly.
- For Seedance 2.0 input rules, duration, resolution, face-material restrictions, and other API details, see the local Chinese API documentation files in this repository.
- Model IDs ultimately depend on the models or endpoint IDs enabled in your Volcengine Ark account.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=sihuangtech/seedance-studio&type=Date)](https://www.star-history.com/#sihuangtech/seedance-studio&Date)

## License

MIT. See [LICENSE](LICENSE).
