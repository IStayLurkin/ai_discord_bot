import discord
from discord import app_commands
from discord.ext import commands

from godbot.deterministic.fitness_tools import (
    strength_percentile,
    generate_training_block,
    recommended_volume,
)


class Fitness(commands.Cog):
    """Fitness slash commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="percentile", description="Strength percentile")
    async def percentile(
        self,
        interaction: discord.Interaction,
        lift: str,
        weight: float,
        bodyweight: float,
    ):
        p = strength_percentile(lift, weight, bodyweight)
        await interaction.response.send_message(f"{lift.title()} percentile: {p}")

    @app_commands.command(
        name="trainingblock",
        description="Generate a deterministic training program",
    )
    async def trainingblock(
        self, interaction: discord.Interaction, style: str, experience: str
    ):
        block = generate_training_block(style, experience)
        await interaction.response.send_message(str(block))

    @app_commands.command(
        name="volume", description="Weekly volume recommendation (sets)"
    )
    async def volume(
        self, interaction: discord.Interaction, muscle: str, experience: str
    ):
        vol = recommended_volume(muscle, experience)
        await interaction.response.send_message(str(vol))


async def setup(bot):
    await bot.add_cog(Fitness(bot))

