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
        label="A name for this account, e.g. 'Account 1'",
        firm="Prop firm name, e.g. Apex, TopStep, FTMO",
        account_size="Starting balance in dollars e.g. 50000",
        daily_loss_limit="Max dollars you're allowed to lose in one day e.g. 1000",
        max_loss_limit="Max dollar drawdown allowed",
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
        max_loss_limit: float,
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
                max_drawdown=max_loss_limit,
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
            embed.add_field(name="Max loss limit", value=f"${max_loss_limit:,.2f} ({drawdown_type.value})")
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

            total_pnl = sum(acc.current_balance - acc.account_size for acc in accounts)
            color = discord.Color.green() if total_pnl >= 0 else discord.Color.red()

            embed = discord.Embed(
                title="Your accounts",
                description=f"Total P&L across all accounts: **${total_pnl:,.2f}**",
                color=color,
            )
            for acc in accounts:
                pnl = acc.current_balance - acc.account_size
                progress = pnl / acc.profit_target * 100
                embed.add_field(
                    name=f"{acc.label} ({acc.firm})",
                    value=(
                        f"P&L: ${pnl:,.2f}\n"
                        f"Balance: ${acc.current_balance:,.2f}\n"
                        f"{progress:.1f}% to target"
                    ),
                    inline=True,
                )
            await interaction.response.send_message(embed=embed)
        finally:
            session.close()
    async def account_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
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
        except Exception as e:
            print(f"AUTOCOMPLETE ERROR: {e}")
            import traceback
            traceback.print_exc()
            return []

    @app_commands.command(name="trade_log", description="Log a completed trade.")
    @app_commands.describe(
        screenshot="Optional: a chart screenshot for this trade",
        account="Which account this trade belongs to",
        symbol="Symbol, e.g. MNQ, NES",
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
        screenshot: discord.Attachment = None,
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
                screenshot_url=screenshot.url if screenshot else None,
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

            if screenshot:
                embed.set_image(url=screenshot.url)

            await interaction.response.send_message(embed=embed)
        finally:
            session.close()

    @app_commands.command(name="trade_stats", description="See win rate and stats for an account.")
    @app_commands.describe(account="Which account to see stats for")
    @app_commands.autocomplete(account=account_autocomplete)
    async def trade_stats(self, interaction: discord.Interaction, account: str):
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

            trades = (
                session.query(Trade)
                .filter(Trade.account_id == acc.id)
                .order_by(Trade.created_at.asc())
                .all()
            )

            if not trades:
                await interaction.response.send_message(
                    f"No trades logged yet for '{account}'. Use `/trade_log` to add one.",
                    ephemeral=True,
                )
                return

            total_trades = len(trades)
            wins = [t for t in trades if t.pnl > 0]
            losses = [t for t in trades if t.pnl < 0]
            win_rate = len(wins) / total_trades * 100

            gross_win = sum(t.pnl for t in wins)
            gross_loss = abs(sum(t.pnl for t in losses))
            profit_factor = gross_win / gross_loss if gross_loss > 0 else float("inf")

            best_trade = max(trades, key=lambda t: t.pnl)
            worst_trade = min(trades, key=lambda t: t.pnl)
            total_pnl = sum(t.pnl for t in trades)

            streak_count = 0
            streak_type = None
            for t in reversed(trades):
                current_type = "win" if t.pnl > 0 else "loss" if t.pnl < 0 else "breakeven"
                if streak_type is None:
                    streak_type = current_type
                    streak_count = 1
                elif current_type == streak_type:
                    streak_count += 1
                else:
                    break

            embed = discord.Embed(
                title=f"Stats for {acc.label}",
                color=discord.Color.green() if total_pnl >= 0 else discord.Color.red(),
            )
            embed.add_field(name="Total trades", value=str(total_trades), inline=True)
            embed.add_field(name="Win rate", value=f"{win_rate:.1f}%", inline=True)
            embed.add_field(
                name="Profit factor",
                value="∞" if profit_factor == float("inf") else f"{profit_factor:.2f}",
                inline=True,
            )
            embed.add_field(name="Total P&L", value=f"${total_pnl:,.2f}", inline=True)
            embed.add_field(name="Best trade", value=f"${best_trade.pnl:,.2f} ({best_trade.symbol})", inline=True)
            embed.add_field(name="Worst trade", value=f"${worst_trade.pnl:,.2f} ({worst_trade.symbol})", inline=True)
            embed.add_field(
                name="Current streak",
                value=f"{streak_count} {streak_type}{'s' if streak_count != 1 else ''}",
                inline=True,
            )

            await interaction.response.send_message(embed=embed)
        finally:
            session.close()
async def setup(bot: commands.Bot):
    await bot.add_cog(Trades(bot))

