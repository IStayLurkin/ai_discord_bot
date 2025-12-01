import discord

from deterministic.wildrift_matchup import full_matchup_report


def register_wildrift_commands(client: discord.Client) -> None:
    tree = client.tree

    @tree.command(
        name="wr_vs",
        description="Analyze a Wild Rift matchup (deterministic).",
    )
    async def wr_vs_cmd(
        interaction: discord.Interaction,
        your_champion: str,
        enemy1: str,
        enemy2: str,
        enemy3: str,
        enemy4: str,
        enemy5: str,
    ):
        enemy_team = [enemy1, enemy2, enemy3, enemy4, enemy5]
        report = full_matchup_report(your_champion, enemy_team)
        await interaction.response.send_message(f"```{report}```")

