import discord
from discord import app_commands
from discord.ext import commands

from godbot.deterministic.nutrition_tools import (
    calculate_macros,
    meal_plan_7_day,
    grocery_list_from_plan,
)


class Nutrition(commands.Cog):
    """Nutrition slash commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="macros", description="Calculate macros based on TDEE & goal")
    async def macros(
        self, interaction: discord.Interaction, tdee: int, goal: str
    ):
        calc = calculate_macros(tdee, goal)
        await interaction.response.send_message(str(calc))

    @app_commands.command(name="mealplan", description="Deterministic 7-day meal plan")
    async def mealplan(
        self, interaction: discord.Interaction, tdee: int, goal: str
    ):
        macros = calculate_macros(tdee, goal)
        plan = meal_plan_7_day(macros)
        await interaction.response.send_message(str(plan))

    @app_commands.command(name="groceries", description="Generate grocery list from plan")
    async def groceries(self, interaction: discord.Interaction, tdee: int, goal: str):
        macros = calculate_macros(tdee, goal)
        plan = meal_plan_7_day(macros)
        groceries = grocery_list_from_plan(plan)
        await interaction.response.send_message(str(groceries))


async def setup(bot):
    await bot.add_cog(Nutrition(bot))

