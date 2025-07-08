"""
Leaderboard Database Manager
"""

import aiosqlite
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from models import Deal, LeaderboardEntry

logger = logging.getLogger(__name__)

class LeaderboardDatabase:
    """Handles all database operations for the leaderboard system"""
    
    def __init__(self):
        self.db_path = 'danny_bot.db'
    
    async def setup_database(self):
        """Initialize leaderboard database tables with a clean and correct schema."""
        async with aiosqlite.connect(self.db_path) as db:
            # Drop existing tables to ensure a fresh start if schema is wrong
            await db.execute('DROP TABLE IF EXISTS deals')
            await db.execute('DROP TABLE IF EXISTS leaderboard_snapshots')
            await db.execute('DROP TABLE IF EXISTS tournament_weeks')

            # Deals table - Main table for all deals
            await db.execute('''
                CREATE TABLE deals (
                    deal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    deal_type TEXT NOT NULL,
                    niche TEXT NOT NULL DEFAULT 'solar',
                    points INTEGER NOT NULL,
                    description TEXT,
                    additional_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified BOOLEAN DEFAULT 1,
                    disputed BOOLEAN DEFAULT 0,
                    week_number INTEGER NOT NULL,
                    admin_submitted BOOLEAN DEFAULT 0,
                    admin_user_id INTEGER
                )
            ''')
            
            # Leaderboard snapshots table
            await db.execute('''
                CREATE TABLE leaderboard_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    niche TEXT NOT NULL DEFAULT 'solar',
                    total_points INTEGER NOT NULL,
                    standard_deals INTEGER NOT NULL,
                    self_generated_deals INTEGER NOT NULL,
                    total_deals INTEGER NOT NULL,
                    rank_position INTEGER NOT NULL,
                    snapshot_date DATE NOT NULL,
                    week_number INTEGER NOT NULL
                )
            ''')
            
            # Disputes table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS disputes (
                    dispute_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    deal_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    admin_decision TEXT,
                    admin_reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_timestamp TIMESTAMP,
                    FOREIGN KEY (deal_id) REFERENCES deals(deal_id)
                )
            ''')
            
            # Tournament weeks table
            await db.execute('''
                CREATE TABLE tournament_weeks (
                    guild_id INTEGER NOT NULL,
                    week_number INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    PRIMARY KEY (guild_id, week_number)
                )
            ''')
            
            # Tournament settings table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tournament_settings (
                    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL UNIQUE,
                    current_week INTEGER NOT NULL,
                    week_start_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Leaderboard messages table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS leaderboard_messages (
                    guild_id INTEGER PRIMARY KEY,
                    message_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL
                )
            ''')
            
            await db.commit()
            logger.info("Leaderboard database tables (re)initialized with fresh schema.")
    
    async def insert_deal(self, guild_id: int, user_id: int, username: str, deal_type: str, 
                         niche: str, points: int, description: str, week_number: int,
                         admin_submitted: bool = False, admin_user_id: int = None) -> int:
        """Insert a new deal and return the deal ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO deals (guild_id, user_id, username, deal_type, niche, points, 
                                 description, week_number, admin_submitted, admin_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (guild_id, user_id, username, deal_type, niche, points, description, 
                  week_number, admin_submitted, admin_user_id))
            await db.commit()
            return cursor.lastrowid
    
    async def get_leaderboard_data(self, timeframe: str, guild_id: int, week_number: int = None) -> List[Dict]:
        """Get leaderboard data for specified timeframe"""
        async with aiosqlite.connect(self.db_path) as db:
            if timeframe == 'today':
                cursor = await db.execute('''
                    SELECT user_id, username,
                           SUM(points) as total_points,
                           SUM(CASE WHEN deal_type = 'standard' THEN 1 ELSE 0 END) as standard_deals,
                           SUM(CASE WHEN deal_type = 'self_generated' THEN 1 ELSE 0 END) as self_generated_deals,
                           COUNT(*) as total_deals
                    FROM deals 
                    WHERE guild_id = ? AND DATE(timestamp) = DATE('now') AND verified = 1
                    GROUP BY user_id, username
                    ORDER BY total_points DESC, total_deals DESC
                ''', (guild_id,))
            else:  # week
                if week_number is None:
                    week_number = await self.get_current_week_number(guild_id)
                
                cursor = await db.execute('''
                    SELECT user_id, username,
                           SUM(points) as total_points,
                           SUM(CASE WHEN deal_type = 'standard' THEN 1 ELSE 0 END) as standard_deals,
                           SUM(CASE WHEN deal_type = 'self_generated' THEN 1 ELSE 0 END) as self_generated_deals,
                           COUNT(*) as total_deals
                    FROM deals 
                    WHERE guild_id = ? AND week_number = ? AND verified = 1
                    GROUP BY user_id, username
                    ORDER BY total_points DESC, total_deals DESC
                ''', (guild_id, week_number))
            
            rows = await cursor.fetchall()
            return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    async def get_user_stats(self, user_id: int, guild_id: int) -> Optional[Dict]:
        """Get detailed user statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            current_week = await self.get_current_week_number(guild_id)
            
            # Get all-time stats
            cursor = await db.execute('''
                SELECT 
                    niche,
                    deal_type,
                    COUNT(*) as deal_count,
                    SUM(points) as total_points
                FROM deals 
                WHERE user_id = ? AND guild_id = ? AND verified = 1 AND disputed = 0
                GROUP BY niche, deal_type
            ''', (user_id, guild_id))
            
            all_stats = await cursor.fetchall()
            
            # Get current week stats
            cursor = await db.execute('''
                SELECT 
                    niche,
                    deal_type,
                    COUNT(*) as deal_count,
                    SUM(points) as total_points
                FROM deals 
                WHERE user_id = ? AND guild_id = ? AND week_number = ? AND verified = 1 AND disputed = 0
                GROUP BY niche, deal_type
            ''', (user_id, guild_id, current_week))
            
            week_stats = await cursor.fetchall()
            
            if not all_stats and not week_stats:
                return None
            
            return {
                'all_time': all_stats,
                'current_week': week_stats,
                'week_number': current_week
            }
    
    async def get_current_week_number(self, guild_id: int) -> int:
        """Get current week number for guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT current_week FROM tournament_settings WHERE guild_id = ? ORDER BY setting_id DESC LIMIT 1', 
                (guild_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 1
    
    async def get_week_start_date(self, guild_id: int) -> str:
        """Get start date of current week"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT week_start_date FROM tournament_settings WHERE guild_id = ? ORDER BY setting_id DESC LIMIT 1', 
                (guild_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else datetime.now().strftime('%Y-%m-%d')
    
    async def initialize_tournament_week(self, guild_id: int, week_number: int, start_date: str):
        """Initialize a tournament week"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR IGNORE INTO tournament_weeks (guild_id, week_number, start_date)
                VALUES (?, ?, ?)
            ''', (guild_id, week_number, start_date))
            await db.commit()
    
    async def save_leaderboard_snapshot(self, guild_id: int, leaderboard_data: List[Dict], 
                                      week_number: int, snapshot_date: str):
        """Save a leaderboard snapshot"""
        async with aiosqlite.connect(self.db_path) as db:
            for entry in leaderboard_data:
                await db.execute('''
                    INSERT OR REPLACE INTO leaderboard_snapshots 
                    (guild_id, user_id, username, total_points, standard_deals, self_generated_deals, 
                     total_deals, rank_position, snapshot_date, week_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (guild_id, entry['user_id'], entry['username'], entry['total_points'], 
                      entry['standard_deals'], entry['self_generated_deals'], entry['total_deals'], 
                      entry.get('rank', 0), snapshot_date, week_number))
            await db.commit()
    
    async def get_server_deal_number(self, guild_id: int, global_deal_id: int) -> int:
        """Get server-specific deal number"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) FROM deals 
                WHERE guild_id = ? AND deal_id <= ?
            ''', (guild_id, global_deal_id))
            result = await cursor.fetchone()
            return result[0] if result else 0 