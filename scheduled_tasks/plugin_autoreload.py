# scheduled_tasks/plugin_autoreload.py
async def plugin_autoreload(bot):
    bot.plugins.auto_update()
    print("[Scheduled] Plugin hot reload check executed")

