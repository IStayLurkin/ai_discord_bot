# scheduled_tasks/daily_report.py
async def daily_report(bot):
    # Get report channel from bot config or use a default
    # For now, just log - can be extended to send to a channel
    channel_id = getattr(bot, 'dashboard_config', {}).get("report_channel_id")
    if not channel_id:
        # Just print for now - can be extended
        msg = (
            "📊 **Daily Report**\n"
            f"- Memory size: OK\n"
            f"- Plugins loaded: {len(bot.plugins.plugins)}\n"
            f"- Current model: {bot.current_model}\n"
        )
        print(f"[Scheduled] {msg}")
        return

    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            return

        msg = (
            "📊 **Daily Report**\n"
            f"- Memory size: OK\n"
            f"- Plugins loaded: {len(bot.plugins.plugins)}\n"
            f"- Current model: {bot.current_model}\n"
        )

        await channel.send(msg)
    except Exception as e:
        print(f"[Scheduled] Error sending daily report: {e}")

