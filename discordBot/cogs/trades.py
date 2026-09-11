import datetime
import discord
from discord import app_commands
from discord.ext import commands

from database import get_session
from models import Account, Trade


class Trades(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="account_create", description="Create a new combine/account to track.")
    @app_commands.describe(
        label="A name for this account, e.g. 'Apex 50k Eval #1'",
        firm="Prop firm name, e.g. Apex, TopStep, FTMO",
        account_size="Starting balance in dollars",
        daily_loss_limit="Max dollars you're allowed to lose in one day",
        max_drawdown="Max dollar drawdown allowed",
        drawdown_type="Whether the drawdown trails your equity or is fixed",
        profit_target="Dollar profit needed to pass the evaluation",
    )
    @app_commands.choices(drawdown_type=[
        app_commands.Choice(name="Trailing", value="trailing"),
        app_commands.Choice(name="Static", value="static"),
    ])
    async def account_create(
        self,
        interaction: discord.Interaction,
        label: str,
        firm: str,
        account_size: float,
        daily_loss_limit: float,
        max_drawdown: float,
        profit_target: float,
        drawdown_type: app_commands.Choice[str],
    ):
        session = get_session()
        try:
            account = Account(
                discord_user_id=str(interaction.user.id),
                label=label,
                firm=firm,
                account_size=account_size,
                daily_loss_limit=daily_loss_limit,
                max_drawdown=max_drawdown,
                drawdown_type=drawdown_type.value,
                profit_target=profit_target,
                current_balance=account_size,
                high_water_mark=account_size,
            )
            session.add(account)
            session.commit()

            embed = discord.Embed(
                title=f"✅ Account created: {label}",
                color=discord.Color.green(),
            )
            embed.add_field(name="Firm", value=firm)
            embed.add_field(name="Size", value=f"${account_size:,.2f}")
            embed.add_field(name="Daily loss limit", value=f"${daily_loss_limit:,.2f}")
            embed.add_field(name="Max drawdown", value=f"${max_drawdown:,.2f} ({drawdown_type.value})")
            embed.add_field(name="Profit target", value=f"${profit_target:,.2f}")
            await interaction.response.send_message(embed=embed)
        finally:
            session.close()

    @app_commands.command(name="account_list", description="List your tracked accounts.")
    async def account_list(self, interaction: discord.Interaction):
        session = get_session()
        try:
            accounts = (
                session.query(Account)
                .filter_by(discord_user_id=str(interaction.user.id), is_active=True)
                .all()
            )
            if not accounts:
                await interaction.response.send_message(
                    "You don't have any accounts yet. Create one with `/account_create`.",
                    ephemeral=True,
                )
                return

            embed = discord.Embed(title="Your accounts", color=discord.Color.blurple())
            for acc in accounts:
                progress = (acc.current_balance - acc.account_size) / acc.profit_target * 100
                embed.add_field(
                    name=f"{acc.label} ({acc.firm})",
                    value=(
                        f"Balance: ${acc.current_balance:,.2f}\n"
                        f"Progress to target: {progress:.1f}%\n"
                        f"Phase: {acc.phase}"
                    ),
                    inline=False,
                )
            await interaction.response.send_message(embed=embed)
        finally:
            session.close()

    async def account_autocomplete(self, interaction: discord.Interaction, current: str):
        session = get_session()
        try:
            accounts = (
                session.query(Account)
                .filter_by(discord_user_id=str(interaction.user.id), is_active=True)
                .all()
            )
            return [
                app_commands.Choice(name=acc.label, value=acc.label)
                for acc in accounts
                if current.lower() in acc.label.lower()
            ][:25]
        finally:
            session.close()

    @app_commands.command(name="trade_log", description="Log a completed trade.")
    @app_commands.describe(
        account="Which account this trade belongs to",
        symbol="Ticker/contract symbol, e.g. NQ, ES, AAPL",
        side="Long or short",
        pnl="Dollar profit/loss for this trade (negative for a loss)",
        entry_price="Optional: entry price",
        exit_price="Optional: exit price",
        size="Optional: contracts/shares traded",
        tags="Optional: comma-separated tags, e.g. breakout,scalp",
        notes="Optional: any notes about the trade",
    )
    @app_commands.choices(side=[
        app_commands.Choice(name="Long", value="long"),
        app_commands.Choice(name="Short", value="short"),
    ])
    @app_commands.autocomplete(account=account_autocomplete)
    async def trade_log(
        self,
        interaction: discord.Interaction,
        account: str,
        symbol: str,
        side: app_commands.Choice[str],
        pnl: float,
        entry_price: float = None,
        exit_price: float = None,
        size: float = None,
        tags: str = None,
        notes: str = None,
    ):
        session = get_session()
        try:
            acc = (
                session.query(Account)
                .filter_by(discord_user_id=str(interaction.user.id), label=account, is_active=True)
                .first()
            )
            if not acc:
                await interaction.response.send_message(
                    f"Couldn't find an account called '{account}'. Use `/account_list` to check your accounts.",
                    ephemeral=True,
                )
                return

            trade = Trade(
                account_id=acc.id,
                symbol=symbol.upper(),
                side=side.value,
                entry_price=entry_price,
                exit_price=exit_price,
                size=size,
                pnl=pnl,
                tags=tags,
                notes=notes,
                trade_date=datetime.date.today(),
            )
            session.add(trade)

            acc.current_balance += pnl
            if acc.current_balance > acc.high_water_mark:
                acc.high_water_mark = acc.current_balance

            session.commit()

            warnings = []

            today_pnl = (
                session.query(Trade)
                .filter(Trade.account_id == acc.id, Trade.trade_date == datetime.date.today())
                .all()
            )
            today_total = sum(t.pnl for t in today_pnl)
            if today_total < 0:
                loss_used = abs(today_total)
                remaining = acc.daily_loss_limit - loss_used
                if remaining <= 0:
                    warnings.append(f"🚨 **Daily loss limit breached.** Used ${loss_used:,.2f} of ${acc.daily_loss_limit:,.2f}.")
                elif remaining <= acc.daily_loss_limit * 0.2:
                    warnings.append(f"⚠️ Only ${remaining:,.2f} left before your daily loss limit.")

            if acc.drawdown_type == "trailing":
                floor = acc.high_water_mark - acc.max_drawdown
            else:
                floor = acc.account_size - acc.max_drawdown
            if acc.current_balance <= floor:
                warnings.append(f"🚨 **Max drawdown breached.** Balance ${acc.current_balance:,.2f} is at/below the floor of ${floor:,.2f}.")
            elif acc.current_balance - floor <= acc.max_drawdown * 0.2:
                warnings.append(f"⚠️ Getting close to max drawdown. ${acc.current_balance - floor:,.2f} of cushion left.")

            if acc.current_balance - acc.account_size >= acc.profit_target:
                warnings.append(f"🎉 **Profit target reached!** You're at ${acc.current_balance:,.2f}.")

            color = discord.Color.red() if pnl < 0 else discord.Color.green()
            embed = discord.Embed(
                title=f"Trade logged: {symbol.upper()} ({side.value})",
                color=color,
            )
            embed.add_field(name="P&L", value=f"${pnl:,.2f}")
            embed.add_field(name="New balance", value=f"${acc.current_balance:,.2f}")
            if warnings:
                embed.add_field(name="Rule status", value="\n".join(warnings), inline=False)

            await interaction.response.send_message(embed=embed)
        finally:
            session.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(Trades(bot))