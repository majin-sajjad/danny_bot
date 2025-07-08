"""
Playground Database Manager
"""

import aiosqlite
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime
from models import CustomPersonality, PracticeSession

logger = logging.getLogger(__name__)

class PlaygroundDatabase:
    """Handles all database operations for the playground system"""
    
    def __init__(self):
        self.db_path = 'danny_bot.db'
    
    async def setup_database(self):
        """Initialize playground database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Custom personalities table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS custom_personalities (
                    personality_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    system_prompt TEXT NOT NULL,
                    conversation_starters TEXT NOT NULL,
                    personality_traits TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    usage_count INTEGER DEFAULT 0
                )
            ''')
            
            # Custom practice sessions table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS custom_practice_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    personality_id INTEGER NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    final_score INTEGER,
                    conversation_count INTEGER DEFAULT 0,
                    FOREIGN KEY (personality_id) REFERENCES custom_personalities(personality_id)
                )
            ''')
            
            await db.commit()
            logger.info("Playground database tables initialized")
    
    async def save_personality(self, user_id: int, name: str, description: str, 
                              system_prompt: str, conversation_starters: List[str],
                              personality_traits: Dict) -> int:
        """Save a new custom personality"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO custom_personalities 
                (user_id, name, description, system_prompt, conversation_starters, personality_traits)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, name, description, system_prompt, 
                  json.dumps(conversation_starters), json.dumps(personality_traits)))
            await db.commit()
            return cursor.lastrowid
    
    async def get_personality(self, personality_id: int) -> Optional[CustomPersonality]:
        """Get a custom personality by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT personality_id, user_id, name, description, system_prompt, 
                       conversation_starters, personality_traits, created_at
                FROM custom_personalities 
                WHERE personality_id = ? AND is_active = 1
            ''', (personality_id,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return CustomPersonality(
                        personality_id=row[0],
                        user_id=row[1],
                        name=row[2],
                        description=row[3],
                        system_prompt=row[4],
                        conversation_starters=json.loads(row[5]),
                        personality_traits=json.loads(row[6]),
                        created_at=row[7]
                    )
                return None
    
    async def get_user_personalities(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all personalities created by a user"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT personality_id, name, description, created_at, usage_count
                FROM custom_personalities 
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit)) as cursor:
                rows = await cursor.fetchall()
                
                personalities = []
                for row in rows:
                    personalities.append({
                        'personality_id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'created_at': row[3],
                        'usage_count': row[4]
                    })
                
                return personalities
    
    async def delete_personality(self, personality_id: int, user_id: int) -> bool:
        """Delete a personality (soft delete by marking inactive)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                UPDATE custom_personalities 
                SET is_active = 0 
                WHERE personality_id = ? AND user_id = ?
            ''', (personality_id, user_id))
            await db.commit()
            return cursor.rowcount > 0
    
    async def update_personality_usage(self, personality_id: int):
        """Increment usage count for a personality"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE custom_personalities 
                SET usage_count = usage_count + 1
                WHERE personality_id = ?
            ''', (personality_id,))
            await db.commit()
    
    async def create_practice_session(self, session_id: str, user_id: int, personality_id: int) -> bool:
        """Create a new practice session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO custom_practice_sessions (session_id, user_id, personality_id)
                    VALUES (?, ?, ?)
                ''', (session_id, user_id, personality_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating practice session: {e}")
            return False
    
    async def end_practice_session(self, session_id: str, final_score: int = None) -> bool:
        """End a practice session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE custom_practice_sessions 
                    SET end_time = CURRENT_TIMESTAMP, final_score = ?
                    WHERE session_id = ?
                ''', (final_score, session_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error ending practice session: {e}")
            return False
    
    async def update_session_stats(self, session_id: str):
        """Update session conversation count"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE custom_practice_sessions 
                    SET conversation_count = conversation_count + 1
                    WHERE session_id = ?
                ''', (session_id,))
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating session stats: {e}")
    
    async def get_active_sessions(self) -> List[Dict]:
        """Get all active practice sessions for session recovery"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row 
                async with db.execute('''
                    SELECT 
                        s.session_id, s.user_id, s.start_time,
                        p.personality_id, p.name, p.description, p.system_prompt, p.personality_traits
                    FROM custom_practice_sessions AS s
                    JOIN custom_personalities AS p ON s.personality_id = p.personality_id
                    WHERE s.end_time IS NULL
                ''') as cursor:
                    rows = await cursor.fetchall()
                    
                    sessions = []
                    for row in rows:
                        session_data = {
                            'session_id': row['session_id'],
                            'user_id': row['user_id'],
                            'personality_id': row['personality_id'],
                            'start_time': row['start_time'],
                            'homeowner_data': {
                                'name': row['name'],
                                'description': row['description'],
                                'system_prompt': row['system_prompt'],
                                'personality_traits': json.loads(row['personality_traits']) if row['personality_traits'] else {}
                            },
                            'conversation_history': []
                        }
                        sessions.append(session_data)
                    
                    return sessions
                    
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    async def get_session_stats(self, user_id: int) -> Dict:
        """Get practice session statistics for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get total sessions
            async with db.execute('''
                SELECT COUNT(*) FROM custom_practice_sessions WHERE user_id = ?
            ''', (user_id,)) as cursor:
                total_sessions = (await cursor.fetchone())[0]
            
            # Get completed sessions
            async with db.execute('''
                SELECT COUNT(*) FROM custom_practice_sessions 
                WHERE user_id = ? AND end_time IS NOT NULL
            ''', (user_id,)) as cursor:
                completed_sessions = (await cursor.fetchone())[0]
            
            # Get average score
            async with db.execute('''
                SELECT AVG(final_score) FROM custom_practice_sessions 
                WHERE user_id = ? AND final_score IS NOT NULL
            ''', (user_id,)) as cursor:
                result = await cursor.fetchone()
                avg_score = result[0] if result[0] is not None else 0
            
            return {
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'average_score': round(avg_score, 1) if avg_score else 0
            } 

    async def create_homeowner(self, homeowner_data: Dict) -> int:
        """Create a new homeowner personality (alias for save_personality)"""
        try:
            # Extract data from homeowner_data dict
            user_id = homeowner_data['creator_id']
            name = homeowner_data['name']
            description = homeowner_data['personality_description']
            niche = homeowner_data.get('niche', 'general')
            background = homeowner_data.get('background_context', '')
            
            # Create a system prompt based on the data
            system_prompt = f"""You are {name}, a homeowner personality for {niche} sales practice.
            
Personality: {description}
Background: {background}
Niche: {niche}

You should respond realistically as this homeowner would, with appropriate objections and reactions for {niche} sales approaches."""
            
            # Create conversation starters based on niche
            conversation_starters = [
                f"Hello, I'm {name}. What can I do for you?",
                "Yes? Can I help you with something?",
                "Good morning, what brings you to my door?"
            ]
            
            # Create personality traits
            personality_traits = {
                'niche': niche,
                'background': background,
                'description': description
            }
            
            # Use the existing save_personality method
            personality_id = await self.save_personality(
                user_id=user_id,
                name=name,
                description=description,
                system_prompt=system_prompt,
                conversation_starters=conversation_starters,
                personality_traits=personality_traits
            )
            
            logger.info(f"Created homeowner personality {name} with ID {personality_id}")
            return personality_id
            
        except Exception as e:
            logger.error(f"Error creating homeowner: {e}")
            raise
    
    async def get_user_homeowners(self, user_id: int) -> List[Dict]:
        """Get user's homeowner personalities (alias for get_user_personalities)"""
        try:
            personalities = await self.get_user_personalities(user_id)
            
            # Convert to homeowner format
            homeowners = []
            for personality in personalities:
                homeowners.append({
                    'id': personality['personality_id'],
                    'name': personality['name'],
                    'niche': 'general',  # Default niche if not specified
                    'personality_description': personality['description'],
                    'created_at': personality['created_at'],
                    'usage_count': personality['usage_count']
                })
            
            return homeowners
            
        except Exception as e:
            logger.error(f"Error getting user homeowners: {e}")
            return [] 