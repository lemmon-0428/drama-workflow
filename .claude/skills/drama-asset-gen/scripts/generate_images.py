#!/usr/bin/env python3
"""
Call gpt-image-2 via MiCu API to generate drama asset images.

Usage:
    python generate_images.py --tasks '<json_array>' --output-dir ./assets

Environment variables:
    IMAGE2_API_KEY   — required, API key for the image generation service
    IMAGE2_BASE_URL  — optional, defaults to https://www.micuapi.ai
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx


API_KEY = os.environ.get("IMAGE2_API_KEY", "")
BASE_URL = (os.environ.get("IMAGE2_BASE_URL") or "https://www.micuapi.ai").rstrip("/")
TIMEOUT = int(os.environ.get("IMAGE2_TIMEOUT_SECONDS", "180"))
MAX_RETRIES = 1

CATEGORY_DIRS = {
    "character": "characters",
    "scene": "scenes",
    "prop": "props",
}


def post_json(url: str, payload: dict) -> dict:
    with httpx.Client(timeout=TIMEOUT, verify=False) as client:
        response = client.post(
            url,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
        )
    if response.status_code >= 400:
        raise httpx.HTTPStatusError(
            f"HTTP {response.status_code}: {response.text}",
            request=response.request,
            response=response,
        )
    return response.json()


def try_responses_api(prompt: str, size: str) -> dict:
    return post_json(f"{BASE_URL}/v1/responses", {
        "model": "gpt-image-2",
        "input": prompt,
        "tools": [{"type": "image_generation", "size": size}],
    })


def try_images_api(prompt: str, size: str) -> dict:
    return post_json(f"{BASE_URL}/v1/images/generations", {
        "model": "gpt-image-2",
        "prompt": prompt,
        "n": 1,
        "size": size,
    })


def extract_image_url(payload: dict) -> str | None:
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if isinstance(item, dict):
                result = item.get("result")
                if isinstance(result, str) and (result.startswith("http") or result.startswith("data:image/")):
                    return result

    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                url = item.get("url")
                if isinstance(url, str):
                    return url
                b64 = item.get("b64_json")
                if isinstance(b64, str):
                    return f"data:image/png;base64,{b64}"

    choices = payload.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if isinstance(choice, dict):
                msg = choice.get("message") or choice.get("delta")
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        match = re.search(r"data:image/[-+.\w]+;base64,[A-Za-z0-9+/=]+", content)
                        if match:
                            return match.group(0)
                        match = re.search(r"!\[[^\]]*]\((https?://[^)\s]+)\)", content)
                        if match:
                            return match.group(1)

    return None


def download_image(image_value: str) -> bytes:
    if image_value.startswith("data:image/"):
        _, encoded = image_value.split(",", 1)
        return base64.b64decode(encoded)

    if image_value.startswith("http"):
        with httpx.Client(timeout=60, verify=False) as client:
            resp = client.get(image_value)
            return resp.content

    return base64.b64decode(image_value)


def generate_one(task: dict, output_dir: Path) -> dict:
    name = task["name"]
    prompt = task["prompt"]
    size = task.get("size", "1024x1024")
    category = task.get("category", "character")

    subdir = output_dir / CATEGORY_DIRS.get(category, category)
    subdir.mkdir(parents=True, exist_ok=True)
    filepath = subdir / f"{name}.png"

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            try:
                resp = try_responses_api(prompt, size)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in {404, 405, 501}:
                    resp = try_images_api(prompt, size)
                else:
                    raise

            image_url = extract_image_url(resp)
            if not image_url:
                raise RuntimeError(f"No image in response: {json.dumps(resp)[:500]}")

            image_bytes = download_image(image_url)
            filepath.write_bytes(image_bytes)

            return {
                "name": name,
                "category": category,
                "path": str(filepath),
                "size": size,
                "prompt": prompt,
                "status": "success",
            }
        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(2)

    return {
        "name": name,
        "category": category,
        "path": str(filepath),
        "size": size,
        "prompt": prompt,
        "status": "failed",
        "error": last_error,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate drama asset images via gpt-image-2")
    parser.add_argument("--tasks", required=True, help="JSON array of task objects")
    parser.add_argument("--output-dir", required=True, help="Output directory for generated images")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: IMAGE2_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)

    tasks = json.loads(args.tasks)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(tasks)

    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{total}] Generating: {task['name']} ({task.get('category', 'unknown')})...")
        result = generate_one(task, output_dir)
        results.append(result)
        if result["status"] == "success":
            print(f"  ✓ Saved to {result['path']}")
        else:
            print(f"  ✗ Failed: {result.get('error', 'unknown')}")

    manifest_path = output_dir / "manifest.json"
    # 与已有清单按 (category, name) 合并，部分重跑时不丢失其他资产的记录
    merged = {}
    if manifest_path.exists():
        try:
            for asset in json.loads(manifest_path.read_text()).get("assets", []):
                merged[(asset.get("category"), asset.get("name"))] = asset
        except (json.JSONDecodeError, OSError):
            pass
    for result in results:
        merged[(result["category"], result["name"])] = result
    assets = list(merged.values())
    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(assets),
        "success": sum(1 for r in assets if r["status"] == "success"),
        "failed": sum(1 for r in assets if r["status"] == "failed"),
        "assets": assets,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"\nManifest saved to {manifest_path}")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
