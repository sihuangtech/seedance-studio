# Seedance Studio

[中文 README](README_zh-CN.md)

Seedance Studio is a Python client project for the Volcengine Ark Seedance video generation API.

It includes:

- Streamlit GUI for creating, querying, listing, cancelling, and deleting tasks
- `SeedanceClient` SDK for programmatic use
- Content helpers for text, images, videos, audio, and draft tasks
- CLI for quick local operations
- Tests based on `httpx.MockTransport`, with no real API calls

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

You can also install from the requirements files:

```powershell
python -m pip install -r requirements-dev.txt
```

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
streamlit run src/gui/app.py
```

After the app starts, open the local browser page and enter your API key, model, prompt, media inputs, and generation settings.

## CLI Examples

Text-to-video:

```powershell
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

## Notes

- Video generation tasks are asynchronous. Create a task first, then query its status.
- Generated video URLs expire. Save or transfer results promptly.
- For Seedance 2.0 input rules, duration, resolution, face-material restrictions, and other API details, see the local Chinese API documentation files in this repository.

## License

MIT. See [LICENSE](LICENSE).
