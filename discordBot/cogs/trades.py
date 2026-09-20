import datetime
import discord
from discord import app_commands
from discord.ext import commands

from database import get_session
from models import Account, Trade
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class BatchTradeModal(discord.ui.Modal, title="Log Multiple Trades"):
    trades_input = discord.ui.TextInput(
        label="One trade per line: Account, PnL, Symbol",
        style=discord.TextStyle.paragraph,
        placeholder="Test Account, 500, NQ\nTest Account, -150",
        required=True,
        max_length=4000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        session = get_session()
        try:
            lines = [l.strip() for l in self.trades_input.value.split("\n") if l.strip()]
            results = []
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) not in (2, 3):
                    results.append(f"❌ Skipped (need 2 or 3 fields): `{line}`")
                    continue

                account_label, pnl_str = parts[0], parts[1]
                symbol = parts[2].upper() if len(parts) == 3 and parts[2] else "N/A"

                try:
                    pnl = float(pnl_str)
                except ValueError:
                    results.append(f"❌ Invalid P&L '{pnl_str}': `{line}`")
                    continue

                acc = (
                    session.query(Account)
                    .filter_by(discord_user_id=str(interaction.user.id), label=account_label, is_active=True)
                    .first()
                )
                if not acc:
                    results.append(f"❌ No account named '{account_label}': `{line}`")
                    continue

                trade = Trade(
                    account_id=acc.id,
                    symbol=symbol,
                    side="long",
                    pnl=pnl,
                    trade_date=datetime.date.today(),
                )
                session.add(trade)
                acc.current_balance += pnl
                if acc.current_balance > acc.high_water_mark:
                    acc.high_water_mark = acc.current_balance
                results.append(f"✅ {account_label}: ${pnl:,.2f} ({symbol})")

            session.commit()

            embed = discord.Embed(title="Batch trade log results", color=discord.Color.blurple())
            embed.description = "\n".join(results)
            await interaction.response.send_message(embed=embed)
        finally:
            session.close()


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
                        f"{progress:.1f}% to target\n"
                        f"Payouts: {acc.payout_count}"
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

    @app_commands.command(name="account_close", description="Close/archive an account (passed, failed, or manual).")
    @app_commands.describe(account="Which account to close", reason="Why you're closing it")
    @app_commands.choices(reason=[
        app_commands.Choice(name="Passed", value="passed"),
        app_commands.Choice(name="Failed", value="failed"),
        app_commands.Choice(name="Manual close", value="manual"),
    ])
    @app_commands.autocomplete(account=account_autocomplete)
    async def account_close(self, interaction: discord.Interaction, account: str, reason: app_commands.Choice[str]):
        session = get_session()
        try:
            acc = (
                session.query(Account)
                .filter_by(discord_user_id=str(interaction.user.id), label=account, is_active=True)
                .first()
            )
            if not acc:
                await interaction.response.send_message(
                    f"Couldn't find an active account called '{account}'.",
                    ephemeral=True,
                )
                return

            acc.is_active = False
            acc.closed_reason = reason.value
            session.commit()

            emoji = {"passed": "🎉", "failed": "💀", "manual": "📁"}[reason.value]
            await interaction.response.send_message(
                f"{emoji} **{acc.label}** closed as **{reason.name}**. It won't show in `/account_list` or `/trade_log` anymore, but its history is preserved."
            )
        finally:
            session.close()

    @app_commands.command(name="account_payout", description="Log a payout received from a funded account.")
    @app_commands.describe(
        account="Which account received a payout",
        amount="Dollar amount of the payout (will be removed from the account's balance)",
    )
    @app_commands.autocomplete(account=account_autocomplete)
    async def account_payout(self, interaction: discord.Interaction, account: str, amount: float):
        session = get_session()
        try:
            acc = (
                session.query(Account)
                .filter_by(discord_user_id=str(interaction.user.id), label=account, is_active=True)
                .first()
            )
            if not acc:
                await interaction.response.send_message(
                    f"Couldn't find an active account called '{account}'.",
                    ephemeral=True,
                )
                return

            acc.payout_count += 1
            acc.current_balance -= amount
            session.commit()

            embed = discord.Embed(
                title=f"💰 Payout logged: {acc.label}",
                color=discord.Color.gold(),
            )
            embed.add_field(name="Payout amount", value=f"${amount:,.2f}")
            embed.add_field(name="New balance", value=f"${acc.current_balance:,.2f}")
            embed.add_field(name="Total payouts", value=str(acc.payout_count))
            await interaction.response.send_message(embed=embed)
        finally:
            session.close()

    async def account_stats_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            session = get_session()
            try:
                accounts = (
                    session.query(Account)
                    .filter_by(discord_user_id=str(interaction.user.id), is_active=True)
                    .all()
                )
                choices = [
                    app_commands.Choice(name="all", value="__all__"),
                    app_commands.Choice(name="all (including closed accounts)", value="__all_history__"),
                ]
                choices += [
                    app_commands.Choice(name=acc.label, value=acc.label)
                    for acc in accounts
                    if current.lower() in acc.label.lower()
                ]
                return choices[:25]
            finally:
                session.close()
        except Exception as e:
            print(f"AUTOCOMPLETE ERROR: {e}")
            import traceback
            traceback.print_exc()
            return []

    @app_commands.command(name="trade_log", description="Log a completed trade.")
    @app_commands.describe(
        account="Which account this trade belongs to",
        side="Long or short",
        pnl="Dollar profit/loss for this trade (negative for a loss)",
        journal="Your notes on why you took this trade, how it felt, lessons learned",
        screenshot="Optional: a chart screenshot for this trade",
        symbol="Optional: ticker/contract symbol, e.g. NQ, ES, AAPL",
        size="Optional: contracts/shares traded",
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
        side: app_commands.Choice[str],
        pnl: float,
        journal: str,
        screenshot: discord.Attachment = None,
        symbol: str = None,
        size: float = None,
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
                symbol=symbol.upper() if symbol else "N/A",
                side=side.value,
                size=size,
                pnl=pnl,
                notes=journal,
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
            title_symbol = f"{symbol.upper()} " if symbol else ""
            embed = discord.Embed(
                title=f"Trade logged: {title_symbol}({side.value})",
                color=color,
            )
            embed.add_field(name="P&L", value=f"${pnl:,.2f}")
            embed.add_field(name="New balance", value=f"${acc.current_balance:,.2f}")
            if journal:
                embed.add_field(name="Journal", value=journal, inline=False)
            if warnings:
                embed.add_field(name="Rule status", value="\n".join(warnings), inline=False)

            if screenshot:
                embed.set_image(url=screenshot.url)

            await interaction.response.send_message(embed=embed)
        finally:
            session.close()

    @app_commands.command(name="trade_log_batch", description="Log multiple trades across one or more accounts at once.")
    async def trade_log_batch(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BatchTradeModal())

    @app_commands.command(name="trade_stats", description="See win rate and stats for an account.")
    @app_commands.describe(account="Which account to see stats for, or 'All accounts'")
    @app_commands.autocomplete(account=account_stats_autocomplete)
    async def trade_stats(self, interaction: discord.Interaction, account: str):
        session = get_session()
        try:
            if account in ("__all__", "__all_history__"):
                if account == "__all_history__":
                    accounts = (
                        session.query(Account)
                        .filter_by(discord_user_id=str(interaction.user.id))
                        .all()
                    )
                else:
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
                account_ids = [acc.id for acc in accounts]
                trades = (
                    session.query(Trade)
                    .filter(Trade.account_id.in_(account_ids))
                    .order_by(Trade.created_at.asc())
                    .all()
                )
                title_label = "All accounts (history)" if account == "__all_history__" else "All accounts"
            else:
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
                title_label = acc.label

            if not trades:
                await interaction.response.send_message(
                    f"No trades logged yet for '{title_label}'. Use `/trade_log` to add one.",
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
                title=f"Stats for {title_label}",
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

    @app_commands.command(name="trade_chart", description="See an equity curve chart for an account.")
    @app_commands.describe(account="Which account to chart, or 'all'")
    @app_commands.autocomplete(account=account_stats_autocomplete)
    async def trade_chart(self, interaction: discord.Interaction, account: str):
        session = get_session()
        try:
            if account in ("__all__", "__all_history__"):
                if account == "__all_history__":
                    accounts = (
                        session.query(Account)
                        .filter_by(discord_user_id=str(interaction.user.id))
                        .all()
                    )
                else:
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
                account_ids = [acc.id for acc in accounts]
                trades = (
                    session.query(Trade)
                    .filter(Trade.account_id.in_(account_ids))
                    .order_by(Trade.created_at.asc())
                    .all()
                )
                title_label = "All accounts (history)" if account == "__all_history__" else "All accounts"
            else:
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
                title_label = acc.label

            if not trades:
                await interaction.response.send_message(
                    f"No trades logged yet for '{title_label}'. Use `/trade_log` to add one.",
                    ephemeral=True,
                )
                return

            cumulative = 0
            points = [0]
            for t in trades:
                cumulative += t.pnl
                points.append(cumulative)

            bg = "#000000"
            line_color = "#00ff9c" if points[-1] >= 0 else "#ff3b5c"
            xs = list(range(len(points)))

            fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150, facecolor=bg)
            ax.set_facecolor(bg)

            # neon glow: stacked wide, faint lines under the main line
            for width, alpha in [(12, 0.04), (8, 0.06), (5, 0.10)]:
                ax.plot(xs, points, color=line_color, linewidth=width, alpha=alpha, solid_capstyle="round")
            ax.plot(xs, points, color=line_color, linewidth=2.2, solid_capstyle="round", zorder=3)

            ax.fill_between(xs, points, 0, where=[p >= 0 for p in points], color="#00ff9c", alpha=0.12, interpolate=True)
            ax.fill_between(xs, points, 0, where=[p < 0 for p in points], color="#ff3b5c", alpha=0.12, interpolate=True)
            ax.axhline(0, color="#555555", linewidth=0.8, linestyle="--")

            # glowing marker + label on the latest point
            ax.scatter([xs[-1]], [points[-1]], s=160, color=line_color, alpha=0.25, zorder=4)
            ax.scatter([xs[-1]], [points[-1]], s=40, color=line_color, edgecolors="white", linewidths=1, zorder=5)
            ax.annotate(
                f"${points[-1]:,.0f}",
                (xs[-1], points[-1]),
                textcoords="offset points",
                xytext=(0, 12) if points[-1] >= points[-2] else (0, -20),
                ha="center",
                color="white",
                fontsize=10,
                fontweight="bold",
            )

            ax.set_title(f"EQUITY CURVE  ·  {title_label}", fontsize=14, fontweight="bold", color="white", pad=14)
            ax.set_xlabel("Trade #", color="#aaaaaa")
            ax.set_ylabel("Cumulative P&L", color="#aaaaaa")
            ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}")
            ax.tick_params(colors="#aaaaaa")
            ax.grid(True, color="#ffffff", alpha=0.07)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            for side in ("left", "bottom"):
                ax.spines[side].set_color("#333333")
            ax.margins(x=0.05, y=0.15)
            fig.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", facecolor=bg)
            plt.close(fig)
            buf.seek(0)

            file = discord.File(buf, filename="equity_curve.png")

            embed = discord.Embed(
                title=f"Equity curve: {title_label}",
                description=f"Total P&L: **${cumulative:,.2f}** over {len(trades)} trades",
                color=discord.Color.green() if cumulative >= 0 else discord.Color.red(),
            )
            embed.set_image(url="attachment://equity_curve.png")

            await interaction.response.send_message(embed=embed, file=file)
        finally:
            session.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(Trades(bot))

