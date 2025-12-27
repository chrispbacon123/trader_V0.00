"""
Cache Manager for Market Data
Optional local caching layer to reduce network calls and improve performance

Usage:
    from cache_manager import CacheManager
    
    cache = CacheManager(enabled=True)
    
    # Try cache first, fetch if miss
    df = cache.get(symbol, start, end, interval)
    if df is None:
        df = fetch_from_network(...)
        cache.put(symbol, start, end, interval, df)
"""

import os
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import pandas as pd


class CacheManager:
    """
    Local file cache for market data
    
    Cache key: (symbol, start_date, end_date, interval)
    Storage: Parquet files in .cache/ directory
    """
    
    def __init__(
        self,
        cache_dir: str = ".cache",
        enabled: bool = False,
        max_age_days: int = 1,
        max_size_mb: int = 100
    ):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory for cache files (relative to cwd or absolute)
            enabled: Whether caching is active (default OFF)
            max_age_days: Maximum age of cached data before refresh
            max_size_mb: Maximum cache size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        self.max_age_days = max_age_days
        self.max_size_mb = max_size_mb
        self._metadata_file = self.cache_dir / "cache_metadata.json"
        
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _make_cache_key(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> str:
        """Generate a unique cache key for the request"""
        key_str = f"{symbol}_{start_date.date()}_{end_date.date()}_{interval}"
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for a cache key"""
        return self.cache_dir / f"{cache_key}.parquet"
    
    def _get_metadata_path(self, cache_key: str) -> Path:
        """Get metadata path for a cache key"""
        return self.cache_dir / f"{cache_key}.meta.json"
    
    def get(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[Tuple[pd.DataFrame, Dict[str, Any]]]:
        """
        Get cached data if available and fresh
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            
        Returns:
            (DataFrame, metadata) if cache hit, None if miss
        """
        if not self.enabled:
            return None
        
        cache_key = self._make_cache_key(symbol, start_date, end_date, interval)
        cache_path = self._get_cache_path(cache_key)
        meta_path = self._get_metadata_path(cache_key)
        
        if not cache_path.exists() or not meta_path.exists():
            return None
        
        # Check freshness
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            cached_at = datetime.fromisoformat(metadata.get('cached_at', '1970-01-01'))
            age = datetime.now() - cached_at
            
            if age.days > self.max_age_days:
                # Cache is stale
                return None
            
            # Load cached data
            df = pd.read_parquet(cache_path)
            
            # Restore DatetimeIndex
            if 'Date' in df.columns:
                df.set_index('Date', inplace=True)
            df.index = pd.to_datetime(df.index)
            
            metadata['cache_hit'] = True
            metadata['cache_age_hours'] = age.total_seconds() / 3600
            
            return df, metadata
            
        except Exception as e:
            # Cache read error - treat as miss
            return None
    
    def put(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        df: pd.DataFrame,
        extra_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Store data in cache
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            df: DataFrame to cache
            extra_metadata: Additional metadata to store
            
        Returns:
            True if cached successfully
        """
        if not self.enabled:
            return False
        
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            cache_key = self._make_cache_key(symbol, start_date, end_date, interval)
            cache_path = self._get_cache_path(cache_key)
            meta_path = self._get_metadata_path(cache_key)
            
            # Reset index to save date column
            df_to_save = df.copy()
            if df_to_save.index.name or not df_to_save.index.is_integer():
                df_to_save = df_to_save.reset_index()
            
            # Save data
            df_to_save.to_parquet(cache_path, index=False)
            
            # Save metadata
            metadata = {
                'symbol': symbol,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'interval': interval,
                'cached_at': datetime.now().isoformat(),
                'rows': len(df),
                'columns': list(df.columns),
                **(extra_metadata or {})
            }
            
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            # Cleanup if over size limit
            self._cleanup_if_needed()
            
            return True
            
        except Exception as e:
            # Cache write failure is non-fatal
            return False
    
    def _cleanup_if_needed(self):
        """Remove old cache files if over size limit"""
        try:
            total_size = sum(
                f.stat().st_size for f in self.cache_dir.glob("*.parquet")
            )
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb > self.max_size_mb:
                # Remove oldest files first
                files = sorted(
                    self.cache_dir.glob("*.parquet"),
                    key=lambda f: f.stat().st_mtime
                )
                
                for f in files[:len(files)//2]:
                    f.unlink()
                    meta = f.with_suffix('.meta.json')
                    if meta.exists():
                        meta.unlink()
                        
        except Exception:
            pass  # Cleanup failure is non-fatal
    
    def clear(self):
        """Clear all cached data"""
        if self.cache_dir.exists():
            for f in self.cache_dir.glob("*.parquet"):
                f.unlink()
            for f in self.cache_dir.glob("*.meta.json"):
                f.unlink()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.cache_dir.exists():
            return {
                'enabled': self.enabled,
                'entries': 0,
                'size_mb': 0
            }
        
        parquet_files = list(self.cache_dir.glob("*.parquet"))
        total_size = sum(f.stat().st_size for f in parquet_files)
        
        return {
            'enabled': self.enabled,
            'cache_dir': str(self.cache_dir),
            'entries': len(parquet_files),
            'size_mb': round(total_size / (1024 * 1024), 2),
            'max_size_mb': self.max_size_mb,
            'max_age_days': self.max_age_days
        }


# Global cache instance (disabled by default)
_cache: Optional[CacheManager] = None


def get_cache(enabled: bool = False) -> CacheManager:
    """Get or create global cache instance"""
    global _cache
    if _cache is None or _cache.enabled != enabled:
        _cache = CacheManager(enabled=enabled)
    return _cache
