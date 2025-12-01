import discord
from discord import app_commands
from discord.ext import commands

from godbot.core.scheduler import scheduler
from godbot.core.logging import get_logger

log = get_logger(__name__)


class SchedulerCommands(commands.Cog):
    """Scheduler Commands (Phase 11.5)."""

    def __init__(self, bot):
        self.bot = bot
        scheduler.start()

    @app_commands.command(name="schedule_list", description="List all scheduled jobs")
    async def schedule_list(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Jobs: {list(scheduler.jobs.keys())}")

    @app_commands.command(name="schedule_remove", description="Remove a scheduled job")
    async def schedule_remove(self, interaction: discord.Interaction, job_id: str):
        ok = scheduler.remove_job(job_id)
        if ok:
            await interaction.response.send_message(f"Removed job: {job_id}")
        else:
            await interaction.response.send_message(f"Job not found: {job_id}")

    @app_commands.command(name="schedule_add", description="Add a job")
    async def schedule_add(
        self,
        interaction: discord.Interaction,
        job_id: str,
        job_type: str,
        value: str,
    ):
        """
        job_type:
            interval  → value = seconds
            once      → value = ISO timestamp
            cron      → value = "0 9 * * 1"
        """
        data = {}

        if job_type == "interval":
            data = {"seconds": int(value)}

        elif job_type == "once":
            data = {"time": value}

        elif job_type == "cron":
            data = {"cron": value}

        else:
            await interaction.response.send_message("Invalid job_type")
            return

        data["message"] = f"Job {job_id} triggered"
        scheduler.add_job(job_id, job_type, data)

        await interaction.response.send_message(f"Added job: {job_id}")


async def setup(bot):
    await bot.add_cog(SchedulerCommands(bot))

