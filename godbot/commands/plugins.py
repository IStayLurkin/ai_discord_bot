import discord
from discord import app_commands
from discord.ext import commands

from godbot.plugins.loader import plugin_manager
from godbot.core.logging import get_logger
log = get_logger(__name__)


class Plugins(commands.Cog):
    """Plugin Management Commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="plugin_list", description="List loaded plugins")
    async def plugin_list(self, interaction: discord.Interaction):
        plugins = plugin_manager.list_plugins()
        await interaction.response.send_message(f"Loaded Plugins: {plugins}")

    @app_commands.command(name="plugin_reload", description="Reload a plugin")
    async def plugin_reload(self, interaction: discord.Interaction, module: str):
        ok = plugin_manager.reload_plugin(module, self.bot)
        if ok:
            await interaction.response.send_message(f"Reloaded plugin: {module}")
        else:
            await interaction.response.send_message(f"Failed to reload: {module}")


async def setup(bot):
    """Setup function for plugin commands cog"""
    await bot.add_cog(Plugins(bot))


def register_plugin_commands(client: discord.Client) -> None:
    """Register plugin management commands"""
    tree = client.tree

    @tree.command(name="plugin_list", description="List loaded plugins")
    async def plugin_list_cmd(interaction: discord.Interaction):
        plugins = plugin_manager.list_plugins()
        await interaction.response.send_message(f"Loaded Plugins: {plugins}")

    @tree.command(name="plugin_reload", description="Reload a plugin")
    async def plugin_reload_cmd(interaction: discord.Interaction, module: str):
        ok = plugin_manager.reload_plugin(module, client)
        if ok:
            await interaction.response.send_message(f"Reloaded plugin: {module}")
        else:
            await interaction.response.send_message(f"Failed to reload: {module}")

