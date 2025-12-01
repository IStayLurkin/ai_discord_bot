"""
Video Generation — Phase 11.9B
Uses StabilityAI SVD (Stable Video Diffusion).
"""

from __future__ import annotations

import torch
import os
from moviepy.editor import ImageSequenceClip
from diffusers import StableVideoDiffusionPipeline
from PIL import Image
import numpy as np

from godbot.core.logging import get_logger

log = get_logger(__name__)


class DiffusionVideoGenerator:
    def __init__(self, model_name: str, device: str = "cuda"):
        self.model_name = model_name
        self.device = device
        self.pipe = None
        self._load()

    # ---------------------------------------------------------
    # Load SVD
    # ---------------------------------------------------------
    def _load(self):
        log.info(f"Loading video diffusion model: {self.model_name}")

        self.pipe = StableVideoDiffusionPipeline.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if "cuda" in self.device else torch.float32,
        )

        if self.device == "cuda":
            self.pipe.to("cuda")

    # ---------------------------------------------------------
    # Generate Video
    # ---------------------------------------------------------
    def generate(self, prompt: str, seed: int = None, frames: int = 16):
        if seed is None:
            seed = torch.seed()

        generator = torch.Generator(device=self.device).manual_seed(seed)

        log.info(f"Generating VIDEO: '{prompt}', frames={frames}, seed={seed}")

        # First step: create base image from text prompt
        # SVD requires an input image, so we generate one first
        img = self._create_base_image(prompt, generator)

        # Second: pass it through SVD (image-to-video)
        output = self.pipe(
            image=img,
            num_frames=frames,
            generator=generator,
        )
        
        # SVD returns frames - handle different output formats
        if hasattr(output, 'frames'):
            video_frames = output.frames[0] if isinstance(output.frames, list) and len(output.frames) > 0 else output.frames
        else:
            video_frames = output
        
        # Convert frames to PIL images if needed
        pil_frames = []
        for f in video_frames:
            if isinstance(f, Image.Image):
                pil_frames.append(f)
            elif isinstance(f, np.ndarray):
                pil_frames.append(Image.fromarray(f))
            else:
                pil_frames.append(Image.fromarray(np.array(f)))

        # Save
        os.makedirs("output", exist_ok=True)
        out_path = f"output/generated_video_{seed}.mp4"

        clip = ImageSequenceClip(pil_frames, fps=8)
        clip.write_videofile(out_path, codec="libx264")

        return out_path

    # ---------------------------------------------------------
    # Use SD to create initial frame
    # ---------------------------------------------------------
    def _create_base_image(self, prompt: str, generator):
        """
        Creates a base image from text prompt using a text-to-image model.
        SVD requires an input image, so we generate one first.
        """
        # Use a simple SD pipeline for the initial image
        # In a full implementation, you'd reuse the image generator
        from diffusers import StableDiffusionPipeline
        
        # Use a lightweight model for the base image
        sd_pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16 if "cuda" in self.device else torch.float32,
        )
        
        if self.device == "cuda":
            sd_pipe.to("cuda")
        
        # Generate base image
        base_image = sd_pipe(
            prompt=prompt,
            generator=generator,
            num_inference_steps=20,
        ).images[0]
        
        # Clean up
        del sd_pipe
        if self.device == "cuda":
            torch.cuda.empty_cache()
        
        return base_image

