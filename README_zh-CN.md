# Seedance Studio

[English README](README.md)

Seedance Studio 是一个面向火山方舟 Seedance 视频生成 API 的 Python 客户端项目，包含：

- Streamlit 图形界面：创建、查询、列表、取消/删除任务
- `SeedanceClient`：创建、查询、列表、取消/删除任务
- 内容构造函数：文本、图片、视频、音频、样片任务
- CLI：快速创建任务、轮询任务、列出任务、删除任务
- 基础测试：使用 `httpx.MockTransport`，不会真实请求 API

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## 配置

复制 `.env.example` 为 `.env`，或直接在终端设置环境变量：

```powershell
$env:SEEDANCE_API_KEY="你的火山方舟 API Key"
```

SDK 默认模型可通过 `SEEDANCE_MODEL` 设置，也可以每次调用时显式传入。
GUI 里的模型下拉候选可通过 `SEEDANCE_MODEL_CHOICES` 配置，多个模型 ID 用英文逗号分隔。

## 图形界面

```powershell
streamlit run src/gui/app.py
```

启动后在浏览器中填写 API Key、模型、提示词、素材和生成参数即可操作任务。

## CLI 示例

文生视频：

```powershell
seedance create --model doubao-seedance-2-0-260128 --prompt "一只小猫在窗边看雨，电影感，柔和光线" --ratio 16:9 --duration 5
```

图生视频首帧：

```powershell
seedance create --model doubao-seedance-2-0-260128 --prompt "镜头缓慢推进，人物微笑" --image-url "https://example.com/first.png" --image-role first_frame
```

查询并轮询直到完成：

```powershell
seedance wait cgt-xxxx --interval 5 --timeout 900
```

列出任务：

```powershell
seedance list --status succeeded --page-size 10
```

取消排队任务或删除已完成记录：

```powershell
seedance delete cgt-xxxx
```

## Python 示例

```python
from core import SeedanceClient, text_content

client = SeedanceClient.from_env()

task = client.create_task(
    model="doubao-seedance-2-0-260128",
    content=[text_content("一只小猫在窗边看雨，电影感，柔和光线")],
    ratio="16:9",
    duration=5,
    generate_audio=True,
)

result = client.wait_for_task(task["id"])
print(result["status"])
print(result.get("content", {}).get("video_url"))
```

## 项目结构

```text
src/
  core/       # SDK 核心：客户端、配置、content 工具、异常
  cli/        # 命令行入口
  gui/        # Streamlit 图形界面模块
tests/
  test_client.py
```

## 注意

- 生成任务是异步接口，创建后需要查询任务状态。
- 生成结果 URL 有有效期，请及时转存。
- Seedance 2.0 系列输入素材、时长、分辨率、真人脸部素材等规则请以目录内 API 文档为准。

## 许可证

MIT。详见 [LICENSE](LICENSE)。
