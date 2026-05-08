from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from core.client import SeedanceClient
from core.content import (
    audio_content,
    draft_task_content,
    file_to_data_url,
    image_content,
    text_content,
    video_content,
)
from core.errors import SeedanceAPIError


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        client = SeedanceClient.from_env()
        with client:
            result = args.func(client, args)
            if result is not None:
                print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (SeedanceAPIError, TimeoutError, ValueError) as exc:
        print(f"seedance: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seedance", description="Seedance video task client")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a video generation task")
    create.add_argument("--model", help="Model ID or endpoint ID")
    create.add_argument("--prompt", help="Text prompt")
    create.add_argument(
        "--image-url",
        action="append",
        default=[],
        help="Image URL, asset ID, or data URL",
    )
    create.add_argument(
        "--image-file",
        action="append",
        default=[],
        help="Local image file converted to data URL before request",
    )
    create.add_argument(
        "--image-role",
        action="append",
        default=[],
        help="Image role: first_frame, last_frame, or reference_image. Repeats per image.",
    )
    create.add_argument(
        "--video-url",
        action="append",
        default=[],
        help="Reference video URL or asset ID",
    )
    create.add_argument(
        "--audio-url",
        action="append",
        default=[],
        help="Reference audio URL, asset ID, or data URL",
    )
    create.add_argument("--draft-task-id", help="Draft task ID for formal video generation")
    add_generation_options(create)
    create.set_defaults(func=create_task)

    get = subparsers.add_parser("get", help="Get one task")
    get.add_argument("task_id")
    get.set_defaults(func=lambda client, args: client.get_task(args.task_id))

    wait = subparsers.add_parser("wait", help="Poll one task until it reaches a terminal status")
    wait.add_argument("task_id")
    wait.add_argument("--interval", type=float, default=5.0)
    wait.add_argument("--timeout", type=float, default=None)
    wait.set_defaults(
        func=lambda client, args: client.wait_for_task(
            args.task_id, interval=args.interval, timeout=args.timeout
        )
    )

    list_cmd = subparsers.add_parser("list", help="List tasks")
    list_cmd.add_argument("--page-num", type=int)
    list_cmd.add_argument("--page-size", type=int)
    list_cmd.add_argument("--status")
    list_cmd.add_argument("--task-id", action="append", dest="task_ids")
    list_cmd.add_argument("--model")
    list_cmd.add_argument("--service-tier")
    list_cmd.set_defaults(func=list_tasks)

    delete = subparsers.add_parser("delete", help="Cancel queued task or delete task record")
    delete.add_argument("task_id")
    delete.set_defaults(func=delete_task)

    return parser


def add_generation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--callback-url")
    parser.add_argument("--return-last-frame", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--service-tier")
    parser.add_argument("--execution-expires-after", type=int)
    parser.add_argument("--generate-audio", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--draft", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--web-search", action="store_true")
    parser.add_argument("--safety-identifier")
    parser.add_argument("--resolution", choices=["480p", "720p", "1080p"])
    parser.add_argument(
        "--ratio",
        choices=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"],
    )
    parser.add_argument("--duration", type=int)
    parser.add_argument("--frames", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--camera-fixed", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--watermark", action=argparse.BooleanOptionalAction, default=None)


def create_task(client: SeedanceClient, args: argparse.Namespace) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    if args.prompt:
        content.append(text_content(args.prompt))

    image_sources = [*args.image_url, *(file_to_data_url(path) for path in args.image_file)]
    for index, source in enumerate(image_sources):
        role = args.image_role[index] if index < len(args.image_role) else None
        content.append(image_content(source, role=role))

    for source in args.video_url:
        content.append(video_content(source))
    for source in args.audio_url:
        content.append(audio_content(source))
    if args.draft_task_id:
        content.append(draft_task_content(args.draft_task_id))

    if not content:
        raise ValueError("At least one content input is required.")

    tools = [{"type": "web_search"}] if args.web_search else None
    return client.create_task(
        model=args.model,
        content=content,
        callback_url=args.callback_url,
        return_last_frame=args.return_last_frame,
        service_tier=args.service_tier,
        execution_expires_after=args.execution_expires_after,
        generate_audio=args.generate_audio,
        draft=args.draft,
        tools=tools,
        safety_identifier=args.safety_identifier,
        resolution=args.resolution,
        ratio=args.ratio,
        duration=args.duration,
        frames=args.frames,
        seed=args.seed,
        camera_fixed=args.camera_fixed,
        watermark=args.watermark,
    )


def list_tasks(client: SeedanceClient, args: argparse.Namespace) -> dict[str, Any]:
    return client.list_tasks(
        page_num=args.page_num,
        page_size=args.page_size,
        status=args.status,
        task_ids=args.task_ids,
        model=args.model,
        service_tier=args.service_tier,
    )


def delete_task(client: SeedanceClient, args: argparse.Namespace) -> dict[str, str]:
    client.delete_task(args.task_id)
    return {"deleted": args.task_id}


if __name__ == "__main__":
    raise SystemExit(main())
