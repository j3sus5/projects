import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    discord_user_id: Mapped[str] = mapped_column(String, index=True)

    label: Mapped[str] = mapped_column(String)
    firm: Mapped[str] = mapped_column(String)
    phase: Mapped[str] = mapped_column(String, default="evaluation")
    payout_count: Mapped[int] = mapped_column(Integer, default=0)

    account_size: Mapped[float] = mapped_column(Float)
    daily_loss_limit: Mapped[float] = mapped_column(Float)
    max_drawdown: Mapped[float] = mapped_column(Float)
    drawdown_type: Mapped[str] = mapped_column(String, default="trailing")
    profit_target: Mapped[float] = mapped_column(Float)

    current_balance: Mapped[float] = mapped_column(Float)
    high_water_mark: Mapped[float] = mapped_column(Float)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    closed_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    trades: Mapped[list["Trade"]] = relationship(back_populates="account", cascade="all, delete-orphan")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)

    symbol: Mapped[str] = mapped_column(String)
    side: Mapped[str] = mapped_column(String)

    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    size: Mapped[float | None] = mapped_column(Float, nullable=True)

    pnl: Mapped[float] = mapped_column(Float)
    tags: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    screenshot_url: Mapped[str | None] = mapped_column(String, nullable=True)
    
    trade_date: Mapped[datetime.date] = mapped_column(Date)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    account: Mapped["Account"] = relationship(back_populates="trades")