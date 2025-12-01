"""
Image Generation — Phase 11.9B
Stable Diffusion XL / SD Turbo / SD 1.5
"""

from __future__ import annotations

import torch
from diffusers import StableDiffusionXLPipeline, StableDiffusionPipeline
from typing import Optional
import os
from PIL import Image

from godbot.core.logging import get_logger

log = get_logger(__name__)


class DiffusionImageGenerator:
    def __init__(self, model_name: str, device: str = "cuda"):
        self.model_name = model_name
        self.device = device
        self.pipe = None
        self._load()

    # ---------------------------------------------------------
    # Model Loader
    # ---------------------------------------------------------
    def _load(self):
        log.info(f"Loading diffusion model: {self.model_name} on {self.device}")

        if "sdxl" in self.model_name or "turbo" in self.model_name:
            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if "cuda" in self.device else torch.float32,
            )
        else:
            self.pipe = StableDiffusionPipeline.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if "cuda" in self.device else torch.float32,
            )

        if self.device == "cuda":
            self.pipe.to("cuda")

    # ---------------------------------------------------------
    # Generate Image
    # ---------------------------------------------------------
    def generate(self, prompt: str, seed: Optional[int] = None):
        if seed is None:
            seed = torch.seed()

        generator = torch.Generator(device=self.device).manual_seed(seed)

        log.info(f"Generating image: prompt='{prompt}', seed={seed}")

        image = self.pipe(
            prompt=prompt,
            generator=generator,
            num_inference_steps=4 if "turbo" in self.model_name else 30,
            guidance_scale=0 if "turbo" in self.model_name else 7.5,
        ).images[0]

        os.makedirs("output", exist_ok=True)
        out_path = f"output/generated_{seed}.png"
        image.save(out_path)

        return out_path

