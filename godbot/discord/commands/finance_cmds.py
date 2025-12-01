import discord
from typing import Optional

from deterministic.finance_tools import summarize_fi_scenarios
from deterministic.nutrition_tools import (
    bmr_mifflin_st_jeor,
    tdee as calc_tdee,
    macro_split,
    calorie_targets,
    strength_level,
    create_training_block,
)


def register_finance_commands(client: discord.Client) -> None:
    tree = client.tree

    @tree.command(
        name="fi",
        description="FIRE / Coast FI / Lean FI summary (deterministic).",
    )
    async def fi_cmd(
        interaction: discord.Interaction,
        current_age: int,
        retire_age: int,
        current_balance: float,
        monthly_contrib: float,
        desired_annual_spend: float,
        lean_annual_spend: Optional[float] = None,
        annual_return: float = 0.07,
        safe_withdrawal_rate: float = 0.04,
        inflation_rate: float = 0.02,
    ):
        """
        Example:
        /fi current_age:31 retire_age:55 current_balance:50000 monthly_contrib:2500 desired_annual_spend:35000
        """
        await interaction.response.defer()

        summary = summarize_fi_scenarios(
            current_age=current_age,
            retire_age=retire_age,
            current_balance=current_balance,
            monthly_contrib=monthly_contrib,
            desired_annual_spend=desired_annual_spend,
            lean_annual_spend=lean_annual_spend,
            annual_return=annual_return,
            safe_withdrawal_rate=safe_withdrawal_rate,
            inflation_rate=inflation_rate,
        )

        await interaction.followup.send(f"```{summary}```")

    @tree.command(
        name="tdee",
        description="Estimate your BMR, TDEE, and calorie targets.",
    )
    async def tdee_cmd(
        interaction: discord.Interaction,
        sex: str,
        age: int,
        height_cm: float,
        weight_kg: float,
        activity_level: str,
    ):
        """
        activity_level: sedentary, light, moderate, heavy, athlete
        """
        sex_clean = sex.strip().lower()
        activity_level_clean = activity_level.strip().lower()

        bmr = bmr_mifflin_st_jeor(weight_kg, height_cm, age, sex_clean)
        tdee_value = calc_tdee(bmr, activity_level_clean)
        targets = calorie_targets(tdee_value)

        msg = (
            f"**TDEE Results**\n"
            f"BMR (Mifflin-St Jeor): **{bmr:.0f} kcal**\n"
            f"Estimated TDEE ({activity_level_clean}): **{tdee_value:.0f} kcal**\n\n"
            f"**Calorie Targets**\n"
            f"Cut: {targets['cut_low']}–{targets['cut_high']} kcal\n"
            f"Maintain: {targets['maintain']} kcal\n"
            f"Bulk: {targets['bulk_low']}–{targets['bulk_high']} kcal"
        )

        await interaction.response.send_message(msg)

    @tree.command(
        name="macros",
        description="Get a simple macro split (protein/fat/carbs) for a calorie target.",
    )
    async def macros_cmd(
        interaction: discord.Interaction,
        calories: int,
        protein_ratio: float = 0.30,
        fat_ratio: float = 0.25,
        carb_ratio: float = 0.45,
    ):
        """
        Ratios should sum ~1.0 (e.g. 0.3 / 0.25 / 0.45).
        """
        split = macro_split(
            calories,
            protein_ratio=protein_ratio,
            fat_ratio=fat_ratio,
            carb_ratio=carb_ratio,
        )

        msg = (
            f"**Macro Split for {calories} kcal**\n"
            f"Protein: **{split['protein_g']} g**\n"
            f"Fat: **{split['fat_g']} g**\n"
            f"Carbs: **{split['carbs_g']} g**"
        )

        await interaction.response.send_message(msg)

    @tree.command(
        name="strength",
        description="Check your strength level vs bodyweight for a lift.",
    )
    async def strength_cmd(
        interaction: discord.Interaction,
        lift_type: str,
        one_rm: float,
        bodyweight: float,
    ):
        """
        lift_type: bench, squat, deadlift
        """
        lift_type_clean = lift_type.strip().lower()
        level, ratio = strength_level(lift_type_clean, one_rm, bodyweight)

        msg = (
            f"**{lift_type_clean.title()} Strength Check**\n"
            f"1RM: **{one_rm:.1f}** at **{bodyweight:.1f}** BW\n"
            f"Ratio: **{ratio:.2f}x bodyweight**\n"
            f"Estimated level: **{level}**"
        )

        await interaction.response.send_message(msg)

    @tree.command(
        name="plan",
        description="Generate a basic training block (PPL / UL / SH).",
    )
    async def plan_cmd(
        interaction: discord.Interaction,
        style: str = "PPL",
    ):
        """
        style: PPL, UL, SH
        """
        block = create_training_block(style)

        if "error" in block:
            await interaction.response.send_message("Unknown style. Use PPL, UL, or SH.")
            return

        lines = [f"**Training Block: {style.upper()}**"]
        for day, exercises in block.items():
            lines.append(f"\n__{day}__")
            for ex in exercises:
                lines.append(f"- {ex}")

        await interaction.response.send_message("\n".join(lines))

