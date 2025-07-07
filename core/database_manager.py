"""
Database manager for Danny Bot.
Handles all database operations including initialization, user management, and data persistence.
"""

import aiosqlite
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations for Danny Bot."""
    
    def __init__(self, db_path: str = 'danny_bot.db'):
        self.db_path = db_path
    
    async def init_database(self):
        """Initialize the database with all required tables"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # User registrations table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS user_registrations (
                        user_id INTEGER PRIMARY KEY,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        phone_number TEXT NOT NULL,
                        email TEXT NOT NULL,
                        company TEXT,
                        niche TEXT DEFAULT 'solar',
                        additional_niches TEXT,
                        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # AI user names table for Danny Pessy AI memory
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS ai_user_names (
                        user_id INTEGER PRIMARY KEY,
                        display_name TEXT NOT NULL,
                        preferred_name TEXT,
                        registered_name TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        first_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Practice sessions table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS practice_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        personality_type TEXT NOT NULL,
                        niche TEXT DEFAULT 'solar',
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        total_messages INTEGER DEFAULT 0,
                        session_score INTEGER,
                        feedback TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES user_registrations (user_id)
                    )
                ''')
                
                # Practice conversations table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS practice_conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        message_type TEXT NOT NULL, -- 'user' or 'ai'
                        message_content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES practice_sessions (session_id),
                        FOREIGN KEY (user_id) REFERENCES user_registrations (user_id)
                    )
                ''')
                
                # Deals table  
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS deals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        niche TEXT NOT NULL DEFAULT 'solar',
                        deal_type TEXT NOT NULL, -- 'setter', 'closer', 'self_generated'
                        deal_value REAL,
                        customer_info TEXT,
                        deal_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        points_awarded INTEGER DEFAULT 0,
                        screenshot_url TEXT,
                        additional_data TEXT, -- JSON for niche-specific data
                        admin_submitted BOOLEAN DEFAULT 0,
                        admin_user_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES user_registrations (user_id)
                    )
                ''')

                # Leaderboard snapshots table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS leaderboard_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        niche TEXT NOT NULL DEFAULT 'solar',
                        snapshot_type TEXT NOT NULL, -- 'weekly', 'monthly', 'all_time'
                        total_points INTEGER DEFAULT 0,
                        total_deals INTEGER DEFAULT 0,
                        rank_position INTEGER,
                        snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        period_start TIMESTAMP,
                        period_end TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user_registrations (user_id)
                    )
                ''')

                # Custom personalities table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS custom_personalities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        system_prompt TEXT NOT NULL,
                        conversation_starters TEXT, -- JSON array
                        personality_traits TEXT, -- JSON object
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user_registrations (user_id)
                    )
                ''')
                
                # Custom personality sessions table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS custom_personality_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        personality_id INTEGER NOT NULL,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        total_messages INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES user_registrations (user_id),
                        FOREIGN KEY (personality_id) REFERENCES custom_personalities (id)
                    )
                ''')
                
                await db.commit()
                logger.info("Database initialized successfully")
                        
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    async def get_or_create_user_name_record(self, user_id: int, display_name: str) -> Dict[str, Any]:
        """Get or create user name record for AI memory"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Check if user exists in name tracking
                cursor = await db.execute('''
                    SELECT user_id, display_name, preferred_name, registered_name, 
                           last_updated, first_interaction 
                    FROM ai_user_names WHERE user_id = ?
                ''', (user_id,))
                record = await cursor.fetchone()
                
                if record:
                    # Update display name if it changed
                    if record[1] != display_name:
                        await db.execute('''
                            UPDATE ai_user_names 
                            SET display_name = ?, last_updated = CURRENT_TIMESTAMP 
                            WHERE user_id = ?
                        ''', (display_name, user_id))
                        await db.commit()
                    
                    return {
                        'user_id': record[0],
                        'display_name': record[1],
                        'preferred_name': record[2],
                        'registered_name': record[3],
                        'last_updated': record[4],
                        'first_interaction': record[5]
                    }
                else:
                    # Create new record
                    await db.execute('''
                        INSERT INTO ai_user_names (user_id, display_name)
                        VALUES (?, ?)
                    ''', (user_id, display_name))
                    await db.commit()
                    
                    return {
                        'user_id': user_id,
                        'display_name': display_name,
                        'preferred_name': None,
                        'registered_name': None,
                        'last_updated': None,
                        'first_interaction': None
                    }
                    
        except Exception as e:
            logger.error(f"Error managing user name record: {e}")
            return {
                'user_id': user_id,
                'display_name': display_name,
                'preferred_name': None,
                'registered_name': None,
                'last_updated': None,
                'first_interaction': None
            }

    async def update_user_registered_name(self, user_id: int, first_name: str, last_name: str):
        """Update the registered name when user completes registration"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                registered_name = f"{first_name} {last_name}"
                
                # Update or insert the registered name
                await db.execute('''
                    INSERT OR REPLACE INTO ai_user_names 
                    (user_id, display_name, registered_name, preferred_name, last_updated)
                    VALUES (
                        ?, 
                        COALESCE((SELECT display_name FROM ai_user_names WHERE user_id = ?), ?),
                        ?, 
                        ?, 
                        CURRENT_TIMESTAMP
                    )
                ''', (user_id, user_id, registered_name, registered_name, first_name))
                await db.commit()
                
                logger.info(f"Updated registered name for user {user_id}: {registered_name}")
                
        except Exception as e:
            logger.error(f"Error updating registered name: {e}")

    async def get_user_preferred_name(self, user_id: int, display_name: str) -> str:
        """Get the preferred name for a user (registered name > preferred name > display name)"""
        try:
            name_record = await self.get_or_create_user_name_record(user_id, display_name)
            
            # Priority: registered_name > preferred_name > display_name
            if name_record.get('registered_name'):
                return name_record['registered_name']
            elif name_record.get('preferred_name'):
                return name_record['preferred_name']
            else:
                return display_name
                
        except Exception as e:
            logger.error(f"Error getting preferred name: {e}")
            return display_name
    
    # User registration operations
    async def get_user_registration(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user registration data"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT user_id, first_name, last_name, phone_number, email, 
                           company, niche, additional_niches, registration_date
                    FROM user_registrations WHERE user_id = ?
                ''', (user_id,))
                record = await cursor.fetchone()
                
                if record:
                    return {
                        'user_id': record[0],
                        'first_name': record[1],
                        'last_name': record[2],
                        'phone_number': record[3],
                        'email': record[4],
                        'company': record[5],
                        'niche': record[6],
                        'additional_niches': record[7],
                        'registration_date': record[8]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting user registration: {e}")
            return None
    
    async def save_user_registration(self, user_id: int, first_name: str, last_name: str, 
                                   phone_number: str, email: str, company: str = None, 
                                   niche: str = 'solar', additional_niches: str = None):
        """Save user registration data"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO user_registrations 
                    (user_id, first_name, last_name, phone_number, email, company, niche, additional_niches)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, first_name, last_name, phone_number, email, company, niche, additional_niches))
                await db.commit()
                
                logger.info(f"Saved registration for user {user_id}: {first_name} {last_name}")
                
        except Exception as e:
            logger.error(f"Error saving user registration: {e}")
            raise
    
    async def delete_user_registration(self, user_id: int):
        """Delete user registration data"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM user_registrations WHERE user_id = ?', (user_id,))
                await db.commit()
                
                logger.info(f"Deleted registration for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error deleting user registration: {e}")
            raise
    
    # Deal operations
    async def save_deal(self, user_id: int, niche: str, deal_type: str, deal_value: float = None,
                       customer_info: str = None, points_awarded: int = 0, 
                       screenshot_url: str = None, additional_data: str = None,
                       admin_submitted: bool = False, admin_user_id: int = None, guild_id: int = 0):
        """Save a new deal"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get user info for the deal
                user_cursor = await db.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
                user_record = await user_cursor.fetchone()
                username = user_record[0] if user_record else f"User_{user_id}"
                
                # Calculate week number
                import datetime
                current_date = datetime.datetime.now()
                week_number = current_date.isocalendar()[1]
                
                cursor = await db.execute('''
                    INSERT INTO deals 
                    (user_id, username, deal_type, points, description, niche, deal_value, 
                     customer_info, screenshot_url, additional_data, admin_submitted, 
                     admin_user_id, deal_date, week_number, guild_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                ''', (user_id, username, deal_type, points_awarded, 
                      customer_info or f"{deal_type} deal", niche, deal_value, 
                      customer_info, screenshot_url, additional_data, admin_submitted, 
                      admin_user_id, week_number, guild_id))
                
                deal_id = cursor.lastrowid
                await db.commit()
                
                logger.info(f"Saved deal {deal_id} for user {user_id}: {niche} {deal_type} in guild {guild_id}")
                return deal_id
                
        except Exception as e:
            logger.error(f"Error saving deal: {e}")
            raise
    
    async def get_user_deals(self, user_id: int, niche: str = None, limit: int = None, guild_id: int = None):
        """Get deals for a user, optionally filtered by niche and guild"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Build query with conditional WHERE clauses
                where_clauses = []
                params = []
                
                if user_id is not None:
                    where_clauses.append("user_id = ?")
                    params.append(user_id)
                
                if niche:
                    where_clauses.append("niche = ?")
                    params.append(niche)
                
                if guild_id is not None:
                    where_clauses.append("guild_id = ?")
                    params.append(guild_id)
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                query = f'''
                    SELECT deal_id, niche, deal_type, deal_value, customer_info, 
                           COALESCE(deal_date, timestamp) as deal_date, 
                           points, admin_submitted, admin_user_id, guild_id
                    FROM deals WHERE {where_clause}
                    ORDER BY COALESCE(deal_date, timestamp) DESC
                '''
                
                if limit:
                    query += f' LIMIT {limit}'
                
                cursor = await db.execute(query, params)
                records = await cursor.fetchall()
                
                deals = []
                for record in records:
                    deals.append({
                        'id': record[0],  # deal_id mapped to id for backward compatibility
                        'niche': record[1],
                        'deal_type': record[2],
                        'deal_value': record[3],
                        'customer_info': record[4],
                        'deal_date': record[5],
                        'points_awarded': record[6],
                        'admin_submitted': record[7],
                        'admin_user_id': record[8],
                        'guild_id': record[9]
                    })
                
                return deals
                
        except Exception as e:
            logger.error(f"Error getting user deals: {e}")
            return [] 