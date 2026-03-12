"""SQLite-based caching system with TTL support."""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration."""
    ttl_prices: int = 3600  # 1 hour for prices
    ttl_fundamentals: int = 86400  # 24 hours for fundamentals
    ttl_news: int = 1800  # 30 minutes for news
    ttl_edgar: int = 604800  # 7 days for SEC filings
    max_entries: int = 10000  # Max cache entries before cleanup


class CacheManager:
    """
    SQLite-based cache manager with TTL support.
    
    Provides intelligent caching for API responses with automatic
    expiration and cleanup to manage database size.
    """
    
    def __init__(self, db_path: str = "./data/cache.db", config: Optional[CacheConfig] = None):
        """
        Initialize cache manager.
        
        Args:
            db_path: Path to SQLite database file
            config: Cache configuration (uses defaults if None)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = config or CacheConfig()
        self._init_db()
        
    def _init_db(self) -> None:
        """Initialize cache database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    ttl_seconds INTEGER NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP
                )
            """)
            
            # Create indices for efficient queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON cache_entries(expires_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_source ON cache_entries(source)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created ON cache_entries(created_at)
            """)
            
            conn.commit()
            logger.info(f"Cache database initialized at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _cleanup_expired(self, conn: sqlite3.Connection) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        cursor = conn.execute(
            "DELETE FROM cache_entries WHERE expires_at < datetime('now')"
        )
        return cursor.rowcount
    
    def _cleanup_oldest(self, conn: sqlite3.Connection, limit: int = 1000) -> int:
        """
        Remove oldest entries when cache is too large.
        
        Args:
            limit: Maximum entries to remove
            
        Returns:
            Number of entries removed
        """
        cursor = conn.execute("""
            DELETE FROM cache_entries 
            WHERE key IN (
                SELECT key FROM cache_entries 
                ORDER BY last_accessed NULLS FIRST, created_at ASC 
                LIMIT ?
            )
        """, (limit,))
        return cursor.rowcount
    
    def _maybe_cleanup(self, conn: sqlite3.Connection) -> None:
        """Run cleanup if cache size exceeds threshold."""
        # Clean up expired entries first
        expired = self._cleanup_expired(conn)
        if expired > 0:
            logger.debug(f"Cleaned up {expired} expired cache entries")
        
        # Check total count
        count = conn.execute(
            "SELECT COUNT(*) FROM cache_entries"
        ).fetchone()[0]
        
        if count > self.config.max_entries:
            to_remove = count - self.config.max_entries + 1000  # Remove extra to avoid frequent cleanup
            removed = self._cleanup_oldest(conn, to_remove)
            logger.info(f"Cache size exceeded limit, removed {removed} oldest entries")
        
        conn.commit()
    
    def get(
        self, 
        key: str, 
        allow_stale: bool = False
    ) -> tuple[Optional[Any], bool]:
        """
        Retrieve item from cache.
        
        Args:
            key: Cache key
            allow_stale: Return data even if expired (with stale=True flag)
            
        Returns:
            Tuple of (data, is_stale) or (None, False) if not found
        """
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT data, expires_at, access_count 
                FROM cache_entries 
                WHERE key = ?
                """,
                (key,)
            ).fetchone()
            
            if row is None:
                return None, False
            
            expires_at = datetime.fromisoformat(row["expires_at"])
            is_expired = expires_at < datetime.utcnow()
            
            if is_expired and not allow_stale:
                # Delete expired entry
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
                return None, False
            
            # Update access statistics
            conn.execute(
                """
                UPDATE cache_entries 
                SET access_count = access_count + 1, last_accessed = datetime('now')
                WHERE key = ?
                """,
                (key,)
            )
            conn.commit()
            
            try:
                data = json.loads(row["data"])
                return data, is_expired
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode cached data for key {key}: {e}")
                return None, False
    
    def set(
        self, 
        key: str, 
        data: Any, 
        source: str,
        ttl: Optional[int] = None
    ) -> None:
        """
        Store item in cache.
        
        Args:
            key: Cache key
            data: Data to cache (must be JSON serializable)
            source: Data source identifier
            ttl: Time-to-live in seconds (uses config default based on source if None)
        """
        # Determine TTL based on source if not specified
        if ttl is None:
            ttl = self._get_default_ttl(source)
        
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        try:
            serialized = json.dumps(data, default=str)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize data for key {key}: {e}")
            return
        
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache_entries 
                (key, data, source, expires_at, ttl_seconds, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, 0, datetime('now'))
                """,
                (key, serialized, source, expires_at.isoformat(), ttl)
            )
            conn.commit()
            
            # Cleanup if needed
            self._maybe_cleanup(conn)
    
    def _get_default_ttl(self, source: str) -> int:
        """Get default TTL based on data source."""
        ttl_map = {
            "yfinance_prices": self.config.ttl_prices,
            "yfinance_fundamentals": self.config.ttl_fundamentals,
            "yfinance_info": self.config.ttl_fundamentals,
            "edgar_filings": self.config.ttl_edgar,
            "edgar_financials": self.config.ttl_edgar,
            "news": self.config.ttl_news,
        }
        return ttl_map.get(source, self.config.ttl_prices)
    
    def delete(self, key: str) -> bool:
        """
        Delete item from cache.
        
        Returns:
            True if item existed and was deleted
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear_source(self, source: str) -> int:
        """
        Clear all entries from a specific source.
        
        Returns:
            Number of entries deleted
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE source = ?",
                (source,)
            )
            conn.commit()
            return cursor.rowcount
    
    def clear_all(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries deleted
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM cache_entries")
            conn.commit()
            return cursor.rowcount
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM cache_entries"
            ).fetchone()[0]
            
            expired = conn.execute(
                "SELECT COUNT(*) FROM cache_entries WHERE expires_at < datetime('now')"
            ).fetchone()[0]
            
            by_source = conn.execute(
                """
                SELECT source, COUNT(*) as count 
                FROM cache_entries 
                GROUP BY source
                """
            ).fetchall()
            
            total_accesses = conn.execute(
                "SELECT SUM(access_count) FROM cache_entries"
            ).fetchone()[0] or 0
            
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
        return {
            "total_entries": total,
            "expired_entries": expired,
            "by_source": {row["source"]: row["count"] for row in by_source},
            "total_accesses": total_accesses,
            "database_size_bytes": db_size,
            "database_size_mb": round(db_size / (1024 * 1024), 2),
        }
    
    def get_cache_key(self, *parts: str) -> str:
        """
        Generate a standardized cache key from parts.
        
        Args:
            *parts: Key components
            
        Returns:
            Normalized cache key
        """
        return ":".join(p.lower().strip() for p in parts)


# Global cache instance
_cache_instance: Optional[CacheManager] = None


def get_cache(db_path: str = "./data/cache.db") -> CacheManager:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager(db_path)
    return _cache_instance
