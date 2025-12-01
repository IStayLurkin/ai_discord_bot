"""
Generation Engine — Phase 11.9A
Unified API for:
    - Image generation
    - Video generation

Backends:
    - Diffusers (Stable Diffusion / SDXL / SVD)

All routing handled here.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from godbot.core.logging import get_logger

log = get_logger(__name__)


GEN_BACKEND = os.getenv("GEN_BACKEND", "diffusers")
GEN_MODEL = os.getenv("GEN_MODEL", "stabilityai/sdxl-turbo")
GEN_VIDEO_MODEL = os.getenv("GEN_VIDEO_MODEL", "stabilityai/stable-video-diffusion-img2vid-xt")
GEN_DEVICE = os.getenv("GEN_DEVICE", "cuda")


class GenerationEngine:
    """Unified interface for GodBot generation features."""

    def __init__(self):
        log.info(f"Generation backend: {GEN_BACKEND}")

        if GEN_BACKEND == "diffusers":
            from godbot.generation.image_gen import DiffusionImageGenerator
            from godbot.generation.video_gen import DiffusionVideoGenerator

            self.image = DiffusionImageGenerator(
                model_name=GEN_MODEL,
                device=GEN_DEVICE,
            )

            self.video = DiffusionVideoGenerator(
                model_name=GEN_VIDEO_MODEL,
                device=GEN_DEVICE,
            )

        else:
            raise ValueError(f"Unknown generation backend: {GEN_BACKEND}")

    # IMAGE
    def generate_image(self, prompt: str, seed: int = None):
        return self.image.generate(prompt, seed=seed)

    # VIDEO
    def generate_video(self, prompt: str, seed: int = None, frames: int = 16):
        return self.video.generate(prompt, seed=seed, frames=frames)


generation_engine = GenerationEngine()

