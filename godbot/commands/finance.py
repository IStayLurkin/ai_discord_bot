import discord
from discord import app_commands
from discord.ext import commands

from godbot.deterministic.finance_tools import (
    coast_fi,
    lean_fi_required,
    safe_withdrawal,
    millionaire_timeline,
    fi_age_projection,
)


class Finance(commands.Cog):
    """Finance-related slash commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="coastfi", description="Calculate Coast FI status")
    async def coastfi(
        self,
        interaction: discord.Interaction,
        current_age: int,
        fire_age: int,
        networth: float,
        spending: float,
    ):
        result = coast_fi(current_age, fire_age, networth, spending)
        await interaction.response.send_message(f"Coast FI:\n{result}")

    @app_commands.command(name="leanfi", description="Required Lean FI number")
    async def leanfi(self, interaction: discord.Interaction, spending: float):
        value = lean_fi_required(spending)
        await interaction.response.send_message(f"Lean FI required: ${value:,.0f}")

    @app_commands.command(name="safewithdrawal", description="Safe monthly withdrawal amount")
    async def safewithdrawal(self, interaction: discord.Interaction, networth: float):
        annual, monthly = safe_withdrawal(networth)
        await interaction.response.send_message(
            f"Annual SWR: ${annual:,.0f}\nMonthly: ${monthly:,.0f}"
        )

    @app_commands.command(name="millionaire", description="Years until inflation-adjusted $1M")
    async def millionaire(
        self,
        interaction: discord.Interaction,
        networth: float,
        monthly_contrib: float,
        roi: float,
        inflation: float,
    ):
        res = millionaire_timeline(networth, monthly_contrib, roi, inflation)
        await interaction.response.send_message(str(res))

    @app_commands.command(
        name="fiage", description="Age when your net worth reaches your FI number"
    )
    async def fiage(
        self,
        interaction: discord.Interaction,
        current_age: int,
        networth: float,
        yearly_contrib: float,
        roi: float,
        target: float,
    ):
        res = fi_age_projection(current_age, networth, yearly_contrib, roi, target)
        await interaction.response.send_message(str(res))


async def setup(bot):
    await bot.add_cog(Finance(bot))

