import discord
from discord import app_commands
from discord.ext import commands

from godbot.generation.engine import generation_engine
from godbot.core.logging import get_logger

log = get_logger(__name__)


class GenerationCommands(commands.Cog):
    """Image & Video Generation Commands (Phase 11.9C)."""

    def __init__(self, bot):
        self.bot = bot

    # ------------------------
    # IMAGE
    # ------------------------
    @app_commands.command(
        name="generate_image",
        description="Generate an image using Stable Diffusion / SDXL",
    )
    async def generate_image(
        self,
        interaction: discord.Interaction,
        prompt: str,
        seed: int = 0,
    ):
        await interaction.response.defer()

        log.info(f"/generate_image prompt='{prompt}', seed={seed}")

        out_path = generation_engine.generate_image(prompt, seed if seed != 0 else None)

        await interaction.followup.send(
            f"Prompt: `{prompt}`",
            file=discord.File(out_path),
        )

    # ------------------------
    # VIDEO
    # ------------------------
    @app_commands.command(
        name="generate_video",
        description="Generate a video using Stable Video Diffusion",
    )
    async def generate_video(
        self,
        interaction: discord.Interaction,
        prompt: str,
        seed: int = 0,
        frames: int = 16,
    ):
        await interaction.response.defer()

        log.info(f"/generate_video prompt='{prompt}', seed={seed}, frames={frames}")

        out_path = generation_engine.generate_video(
            prompt,
            seed if seed != 0 else None,
            frames=frames,
        )

        await interaction.followup.send(
            f"Prompt: `{prompt}`",
            file=discord.File(out_path),
        )


async def setup(bot):
    await bot.add_cog(GenerationCommands(bot))

