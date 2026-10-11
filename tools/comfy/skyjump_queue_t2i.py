#!/usr/bin/env python3
"""Queue SkyJump Animagine XL stills against local ComfyUI (port 8000)."""

from __future__ import annotations

import json
import time
import urllib.request

BASE = "http://127.0.0.1:8000"
NEG = (
    "photorealism, photograph, 3d render, cgi, neon bloom, glossy casino clutter, "
    "fruit slot, UI, HUD, logo, watermark, text, letters, numbers, childish cartoon, "
    "chibi, anime girl, bad anatomy, extra limbs, lowres, blurry, oversaturated, confetti"
)

JOBS = [
    {
        "name": "menu_bg",
        "width": 1344,
        "height": 768,
        "seed": 16092026,
        "positive": (
            "masterpiece, best quality, cinematic winter sports game concept art, "
            "premium ski jumping stadium at blue hour, snow-covered in-run ramp, "
            "floodlights, distant mountains, night navy sky, ice blue highlights, "
            "left third quieter and darker for menu typography, no jumper in the left third, "
            "clean readable illustration, slightly stylized painted look, mature game art, "
            "no UI, no text"
        ),
    },
    {
        "name": "gameplay_bg",
        "width": 1344,
        "height": 768,
        "seed": 16092027,
        "positive": (
            "masterpiece, best quality, view from behind a ski jumper at the very start of the in-run, "
            "camera looking down a long snow ramp into a night stadium, sense of height and distance, "
            "ski flying hill, floodlights, mountains, ice blue and navy palette, "
            "lower 30 percent of the frame is a clean empty snow band with no trees flags or crowd, "
            "space reserved for a horizontal game strip, slightly stylized painted game illustration, "
            "jumper small in foreground wearing helmet and skis, no UI, no text"
        ),
    },
    {
        "name": "jumper_flight",
        "width": 768,
        "height": 768,
        "seed": 16092028,
        "positive": (
            "masterpiece, best quality, full body ski jumper in V-flight pose, helmet visor, "
            "aerodynamic suit, long skis, isolated centered character, solid flat green chroma background, "
            "premium winter sports game illustration, slightly stylized, clean silhouette, no stadium, no text"
        ),
    },
    {
        "name": "jumper_flight_win",
        "width": 768,
        "height": 768,
        "seed": 16092029,
        "positive": (
            "masterpiece, best quality, full body ski jumper in a powerful big-win flight pose, "
            "arms tight, skis in a wide V, helmet, isolated centered character, "
            "solid flat green chroma background, premium winter sports game illustration, no stadium, no text"
        ),
    },
    {
        "name": "jumper_inrun",
        "width": 768,
        "height": 1024,
        "seed": 16092030,
        "positive": (
            "masterpiece, best quality, ski jumper seen from behind at the start gate, crouched inrun pose, "
            "helmet, skis pointing down the ramp, isolated character, solid flat green chroma background, "
            "premium winter sports game illustration, clean silhouette, no stadium, no text"
        ),
    },
    {
        "name": "jumper_menu",
        "width": 768,
        "height": 1024,
        "seed": 16092031,
        "positive": (
            "masterpiece, best quality, ski jumper standing in helmet and skis, three-quarter view, "
            "ready at the top of a hill, isolated character, solid flat green chroma background, "
            "premium winter sports game illustration, clean silhouette, no stadium, no text"
        ),
    },
]


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


def make_prompt(job: dict) -> dict:
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "animagine-xl-3.1.safetensors"},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": job["positive"]},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["1", 1], "text": NEG},
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": job["width"],
                "height": job["height"],
                "batch_size": 1,
            },
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "seed": job["seed"],
                "steps": 24,
                "cfg": 6.0,
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
                "filename_prefix": f"skyjump/{job['name']}",
            },
        },
    }


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


def main() -> None:
    results = []
    for job in JOBS:
        body = post(
            "/prompt",
            {
                "prompt": make_prompt(job),
                "client_id": "skyjump-visual-pass",
            },
        )
        pid = body["prompt_id"]
        print(f"queued {job['name']} {pid}", flush=True)
        item = wait(pid)
        outputs = []
        for node in (item.get("outputs") or {}).values():
            for image in node.get("images") or []:
                outputs.append(
                    f"{image.get('type')}:{image.get('subfolder')}/{image.get('filename')}"
                )
        print(f"done {job['name']} {outputs}", flush=True)
        results.append({"job": job["name"], "prompt_id": pid, "outputs": outputs})
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
