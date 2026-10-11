#!/usr/bin/env python3
"""Follow-up SkyJump stills: stronger gameplay/flight poses + BiRefNet alpha."""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
RAW = Path(r"C:\Users\grzyb\OneDrive\Dokumenty\skifly casino\docs\dev-report\skyjump-comfy-raw")
NEG = (
    "photorealism, photograph, 3d render, cgi, neon bloom, glossy casino clutter, "
    "fruit slot, UI, HUD, logo, watermark, text, letters, numbers, childish cartoon, "
    "chibi, anime girl, bad anatomy, extra limbs, lowres, blurry, standing on ground, "
    "walking, alpine skiing, ski poles"
)


def post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait(prompt_id: str) -> dict:
    for _ in range(240):
        time.sleep(3)
        hist = get(f"/history/{prompt_id}")
        item = hist.get(prompt_id)
        if not item:
            continue
        status = (item.get("status") or {}).get("status_str")
        print(f"  {prompt_id} {status}", flush=True)
        if status == "success":
            return item
        if status == "error":
            raise SystemExit(json.dumps(item.get("status"), indent=2)[:4000])
    raise SystemExit(f"timeout {prompt_id}")


def t2i(name: str, width: int, height: int, seed: int, positive: str) -> None:
    prompt = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "animagine-xl-3.1.safetensors"},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": positive},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": NEG},
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "seed": seed,
                "steps": 28,
                "cfg": 6.5,
                "sampler_name": "euler_ancestral",
                "scheduler": "karras",
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "denoise": 1.0,
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": f"skyjump/{name}",
            },
        },
    }
    pid = post("/prompt", {"prompt": prompt, "client_id": "skyjump-visual-pass"})["prompt_id"]
    print(f"queued {name} {pid}", flush=True)
    wait(pid)


def upload(path: Path) -> str:
    boundary = "----SkyJumpBoundary"
    data = path.read_bytes()
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode("utf-8")
        + data
        + f"\r\n--{boundary}--\r\n".encode("utf-8")
    )
    req = urllib.request.Request(
        BASE + "/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        out = json.loads(resp.read().decode("utf-8"))
    print(f"uploaded {path.name} -> {out}", flush=True)
    return out.get("name") or path.name


def rembg(image_name: str, prefix: str) -> None:
    prompt = {
        "1": {
            "class_type": "LoadBackgroundRemovalModel",
            "inputs": {"bg_removal_name": "birefnet.safetensors"},
        },
        "2": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "3": {
            "class_type": "RemoveBackground",
            "inputs": {"bg_removal_model": ["1", 0], "image": ["2", 0]},
        },
        "4": {"class_type": "InvertMask", "inputs": {"mask": ["3", 0]}},
        "5": {
            "class_type": "JoinImageWithAlpha",
            "inputs": {"image": ["2", 0], "alpha": ["4", 0]},
        },
        "6": {
            "class_type": "SaveImage",
            "inputs": {"images": ["5", 0], "filename_prefix": f"skyjump/{prefix}"},
        },
    }
    pid = post("/prompt", {"prompt": prompt, "client_id": "skyjump-visual-pass"})["prompt_id"]
    print(f"queued rembg {prefix} {pid}", flush=True)
    wait(pid)


def download(filename: str, dest: Path) -> None:
    url = f"{BASE}/view?filename={filename}&subfolder=skyjump&type=output"
    dest.write_bytes(urllib.request.urlopen(url, timeout=30).read())
    print(f"saved {dest} {dest.stat().st_size}", flush=True)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    t2i(
        "gameplay_bg_v2",
        1344,
        768,
        16092101,
        "masterpiece, best quality, cinematic winter sports game concept art, "
        "over-the-shoulder view from behind a ski jumper crouched at the start of a steep in-run, "
        "camera looking DOWN a long snow ramp toward the takeoff table far below, "
        "sense of height and length, night ski jumping stadium, floodlights, distant mountains, "
        "ice blue and navy palette, painted illustration, lower 28 percent is a clean empty snow band "
        "with no trees flags or crowd, no UI, no text",
    )
    t2i(
        "jumper_flight_v2",
        768,
        768,
        16092102,
        "masterpiece, best quality, ski jumper flying through the air in classic V-style, "
        "body almost horizontal, skis in a V behind the jumper, helmet visor, aerodynamic suit, "
        "full body, isolated centered character, solid flat green chroma key background, "
        "premium winter sports game illustration, not standing, not alpine skiing, no poles, no stadium",
    )
    for src, prefix in [
        ("jumper_flight_win_00001_.png", "jumper_flight_win_alpha"),
        ("jumper_menu_00001_.png", "jumper_menu_alpha"),
        ("jumper_inrun_00001_.png", "jumper_inrun_alpha"),
    ]:
        uploaded = upload(RAW / src)
        rembg(uploaded, prefix)

    for name in [
        "gameplay_bg_v2_00001_.png",
        "jumper_flight_v2_00001_.png",
        "jumper_flight_win_alpha_00001_.png",
        "jumper_menu_alpha_00001_.png",
        "jumper_inrun_alpha_00001_.png",
    ]:
        try:
            download(name, RAW / name)
        except Exception as exc:
            print(f"skip {name}: {exc}", flush=True)


if __name__ == "__main__":
    main()
