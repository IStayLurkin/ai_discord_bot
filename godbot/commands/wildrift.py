import discord
from discord import app_commands
from discord.ext import commands

from godbot.deterministic.wildrift_tools import (
    analyze_team_comp,
    cc_density,
    ap_ad_split,
    tankiness,
    counterbuild,
    matchup_advice,
)


class WildRift(commands.Cog):
    """Wild Rift deterministic slash commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="teamcomp", description="Analyze a 5-champion team comp")
    async def teamcomp(
        self,
        interaction: discord.Interaction,
        champ1: str,
        champ2: str,
        champ3: str,
        champ4: str,
        champ5: str,
    ):
        team = [champ1, champ2, champ3, champ4, champ5]
        res = analyze_team_comp(team)
        await interaction.response.send_message(str(res))

    @app_commands.command(name="cc", description="Total CC score of champions")
    async def cc(self, interaction: discord.Interaction, champ1: str, champ2: str):
        res = cc_density([champ1, champ2])
        await interaction.response.send_message(f"CC Density: {res}")

    @app_commands.command(
        name="counterbuild",
        description="Recommended counter-items vs enemy team",
    )
    async def counterbuild_cmd(
        self, interaction: discord.Interaction, champion: str, e1: str, e2: str, e3: str
    ):
        items = counterbuild(champion, [e1, e2, e3])
        await interaction.response.send_message(str(items))

    @app_commands.command(
        name="matchup",
        description="Deterministic lane/jungle matchup guidance",
    )
    async def matchup(self, interaction: discord.Interaction, champ: str, enemy: str):
        note = matchup_advice(champ, enemy)
        await interaction.response.send_message(note)


async def setup(bot):
    await bot.add_cog(WildRift(bot))

