"""SQLAlchemy models for portfolio data persistence."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class CacheEntry(Base):
    """Generic cache for API responses with TTL support."""

    __tablename__ = "cache_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    data = Column(Text, nullable=False)  # JSON serialized
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    source = Column(String(50), nullable=False)  # 'yfinance', 'edgar', etc.
    ttl_seconds = Column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_cache_expires", "expires_at"),
        Index("ix_cache_source", "source"),
    )


class StockPrice(Base):
    """Historical stock price data."""

    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Numeric(15, 4), nullable=False)
    high = Column(Numeric(15, 4), nullable=False)
    low = Column(Numeric(15, 4), nullable=False)
    close = Column(Numeric(15, 4), nullable=False)
    volume = Column(Numeric(20, 0), nullable=False)
    adjusted_close = Column(Numeric(15, 4), nullable=True)

    # Technical indicators (computed on insert)
    sma_20 = Column(Numeric(15, 4), nullable=True)
    sma_50 = Column(Numeric(15, 4), nullable=True)
    sma_200 = Column(Numeric(15, 4), nullable=True)
    ema_12 = Column(Numeric(15, 4), nullable=True)
    ema_26 = Column(Numeric(15, 4), nullable=True)

    __table_args__ = (
        Index("ix_stock_prices_symbol_timestamp", "symbol", "timestamp"),
        Index("ix_stock_prices_timestamp", "timestamp"),
    )


class FundamentalData(Base):
    """Fundamental data cache from Yahoo Finance and EDGAR."""

    __tablename__ = "fundamental_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Company info
    name = Column(String(255), nullable=True)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Numeric(20, 2), nullable=True)
    shares_outstanding = Column(Numeric(20, 0), nullable=True)

    # Valuation
    pe_trailing = Column(Numeric(10, 2), nullable=True)
    pe_forward = Column(Numeric(10, 2), nullable=True)
    peg_ratio = Column(Numeric(10, 2), nullable=True)
    price_to_book = Column(Numeric(10, 2), nullable=True)
    price_to_sales = Column(Numeric(10, 2), nullable=True)
    ev_to_ebitda = Column(Numeric(10, 2), nullable=True)

    # Profitability
    roe = Column(Numeric(10, 4), nullable=True)  # Return on Equity
    roa = Column(Numeric(10, 4), nullable=True)  # Return on Assets
    gross_margin = Column(Numeric(10, 4), nullable=True)
    operating_margin = Column(Numeric(10, 4), nullable=True)
    profit_margin = Column(Numeric(10, 4), nullable=True)

    # Financial Health
    current_ratio = Column(Numeric(10, 2), nullable=True)
    debt_to_equity = Column(Numeric(10, 2), nullable=True)
    quick_ratio = Column(Numeric(10, 2), nullable=True)

    # Growth (YoY)
    revenue_growth = Column(Numeric(10, 4), nullable=True)
    earnings_growth = Column(Numeric(10, 4), nullable=True)

    # Dividend
    dividend_yield = Column(Numeric(10, 4), nullable=True)
    dividend_rate = Column(Numeric(10, 4), nullable=True)

    # Raw JSON for extensibility
    raw_data = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_fundamentals_symbol_fetched", "symbol", "fetched_at"),
    )


class Portfolio(Base):
    """User portfolio definition."""

    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    benchmark_symbol = Column(String(20), default="SPY", nullable=False)

    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioHolding(Base):
    """Individual stock holding within a portfolio."""

    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    shares = Column(Numeric(15, 4), nullable=False)
    average_cost = Column(Numeric(15, 4), nullable=False)
    purchase_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    portfolio = relationship("Portfolio", back_populates="holdings")


# Create engine and session factory for portfolio database
# Using separate SQLite DB for portfolio data
def get_portfolio_engine(db_path: str = "./data/portfolio.db"):
    """Create SQLAlchemy engine for portfolio database."""
    import os
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_database(db_path: str = "./data/portfolio.db"):
    """Initialize database tables."""
    engine = get_portfolio_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_db_session(db_path: str = "./data/portfolio.db"):
    """Get a database session."""
    engine = get_portfolio_engine(db_path)
    SessionLocal.configure(bind=engine)
    return SessionLocal()
