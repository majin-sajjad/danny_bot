"""
AI Engine for Danny Bot - Handles personality-driven conversations
"""

from openai import OpenAI
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from ai_personalities import get_personality, get_available_personalities
from scoring_system import SolarSalesScorer, SessionScore

# Load environment
from dotenv import load_dotenv

class AIEngine:
    """Handles AI conversations with personalities"""
    
    def __init__(self, db_path: str = "danny_bot.db"):
        self.db_path = db_path
        self.active_sessions: Dict[str, dict] = {}
        self.scorer = SolarSalesScorer()
        # Initialize OpenAI client with environment variable
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self._init_tables()
        # 🔧 NEW: Restore active sessions from database on startup
        self._restore_active_sessions()
    
    def _init_tables(self):
        """Initialize database tables - using existing schema from main.py"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Use the existing practice_sessions table structure from main.py
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_practice_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                personality_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                final_score INTEGER DEFAULT NULL,
                end_time TEXT DEFAULT NULL
            )
        ''')
        
        # Add columns if they don't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE ai_practice_sessions ADD COLUMN final_score INTEGER DEFAULT NULL')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE ai_practice_sessions ADD COLUMN end_time TEXT DEFAULT NULL')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_practice(self, user_id: str, personality_type: str) -> Tuple[str, str]:
        """Start a practice session"""
        if personality_type not in get_available_personalities():
            raise ValueError(f"Invalid personality: {personality_type}")
        
        # Create session
        session_id = f"{user_id}_{personality_type}_{int(datetime.now().timestamp())}"
        
        try:
            # Store in database with better connection handling
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO ai_practice_sessions (session_id, user_id, personality_type, start_time)
                VALUES (?, ?, ?, ?)
            ''', (session_id, user_id, personality_type, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            # Get personality and opening message
            personality = get_personality(personality_type)
            self.active_sessions[session_id] = {"personality": personality, "user_id": user_id}
            
            # Generate opening message
            opening_message = self._get_opening_message(personality)
            
            # Store opening message
            self._store_message(session_id, user_id, "ai", opening_message)
            
            return session_id, opening_message
            
        except sqlite3.Error as e:
            print(f"Database error in start_practice: {e}")
            raise ValueError(f"Database error: {e}")
    
    def continue_conversation(self, session_id: str, user_message: str) -> str:
        """Continue a conversation"""
        print(f"DEBUG: continue_conversation called with session_id: {session_id}")
        print(f"DEBUG: active_sessions keys: {list(self.active_sessions.keys())}")
        
        # 🔧 NEW: If session not in active sessions, try to restore it from database
        if session_id not in self.active_sessions:
            print(f"DEBUG: Session {session_id} not found in active_sessions, attempting to restore...")
            if not self._attempt_session_restore(session_id):
                print(f"DEBUG: Failed to restore session {session_id}")
                raise ValueError("Session not found")
        
        session_data = self.active_sessions[session_id]
        personality = session_data["personality"]
        user_id = session_data["user_id"]
        
        print(f"DEBUG: Found session data for {session_id}, personality: {personality.personality_type}")
        
        # Store user message
        self._store_message(session_id, user_id, "user", user_message)
        
        # Generate AI response
        print(f"DEBUG: Generating AI response for message: {user_message[:50]}...")
        ai_response = self._generate_response(personality, user_message, session_id)
        
        print(f"DEBUG: AI response generated: {ai_response[:50]}...")
        
        # Store AI response
        self._store_message(session_id, user_id, "ai", ai_response)
        
        return ai_response
    
    def _get_opening_message(self, personality) -> str:
        """Get opening message from personality"""
        import random
        return random.choice(personality.conversation_starters)
    
    def _generate_response(self, personality, user_message: str, session_id: str) -> str:
        """Generate AI response using OpenAI"""
        try:
            print(f"DEBUG: _generate_response called for personality: {personality.personality_type}")
            
            # Get conversation history
            history = self._get_conversation_history(session_id, limit=4)
            print(f"DEBUG: Retrieved {len(history)} conversation history items")
            
            # Build messages for OpenAI
            messages = [
                {"role": "system", "content": personality.get_system_prompt()}
            ]
            
            # Add history
            for msg in history:
                role = "assistant" if msg["message_type"] == "ai" else "user"
                messages.append({"role": role, "content": msg["content"]})
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            print(f"DEBUG: Sending {len(messages)} messages to OpenAI")
            print(f"DEBUG: System prompt preview: {personality.get_system_prompt()[:100]}...")
            
            # Call OpenAI using the instance client
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content.strip()
            print(f"DEBUG: OpenAI response received: {ai_response[:50]}...")
            
            return ai_response
            
        except Exception as e:
            print(f"DEBUG: OpenAI error in _generate_response: {e}")
            print(f"DEBUG: Error type: {type(e)}")
            return "I'm having technical difficulties. Could you try again?"
    
    def _store_message(self, session_id: str, user_id: str, message_type: str, content: str):
        """Store message in database"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ai_conversation_messages (session_id, user_id, message_type, content)
                VALUES (?, ?, ?, ?)
            ''', (session_id, user_id, message_type, content))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error storing message: {e}")
            # Don't raise here, just log - conversation can continue without storage
    
    def _get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT message_type, content, timestamp
                FROM ai_conversation_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (session_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "message_type": row[0],
                    "content": row[1],
                    "timestamp": row[2]
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"Database error getting history: {e}")
            return []
    
    def get_current_score(self, session_id: str) -> Dict:
        """Get current session score"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session_data = self.active_sessions[session_id]
        personality = session_data["personality"]
        
        # Get conversation history
        history = self._get_conversation_history(session_id)
        
        if len(history) < 2:
            return {"error": "Not enough conversation for scoring"}
        
        try:
            # Use the scoring system
            session_score: SessionScore = self.scorer.evaluate_conversation(
                personality.personality_type,
                history,
                session_data["user_id"]
            )
            
            # Convert to dictionary format
            return {
                "overall_score": session_score.overall_score,
                "percentage": session_score.percentage,
                "grade": session_score.grade,
                "feedback": session_score.solar_specific_feedback,
                "strengths": session_score.strengths,
                "improvements": session_score.improvements,
                "conversation_count": session_score.conversation_count,
                "detailed_breakdown": [
                    {
                        "category": breakdown.category,
                        "score": breakdown.score,
                        "max_score": breakdown.max_score,
                        "feedback": breakdown.feedback,
                        "weight": breakdown.weight
                    }
                    for breakdown in session_score.breakdown
                ]
            }
            
        except Exception as e:
            print(f"Scoring error: {e}")
            return {"error": "Unable to calculate score"}
    
    def end_session(self, session_id: str) -> Dict:
        """End a practice session and return final evaluation"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session_data = self.active_sessions[session_id]
        personality = session_data["personality"]
        
        # Get final evaluation
        try:
            # Get conversation history
            history = self._get_conversation_history(session_id)
            
            # Use the scoring system for final evaluation
            session_score: SessionScore = self.scorer.evaluate_conversation(
                personality.personality_type,
                history,
                session_data["user_id"]
            )
            
            # Generate personality-specific tips
            tips = self._generate_personality_tips(personality.personality_type, session_score)
            
            final_evaluation = {
                "detailed_scores": {
                    breakdown.category: breakdown.score 
                    for breakdown in session_score.breakdown
                },
                "detailed_breakdown": [
                    {
                        "category": breakdown.category,
                        "score": breakdown.score,
                        "max_score": breakdown.max_score,
                        "feedback": breakdown.feedback,
                        "weight": breakdown.weight
                    }
                    for breakdown in session_score.breakdown
                ],
                "overall_score": session_score.overall_score,
                "grade": session_score.grade,
                "percentage": session_score.percentage,
                "summary_feedback": session_score.solar_specific_feedback,
                "strengths": session_score.strengths,
                "areas_for_improvement": session_score.improvements,
                "tips": tips,
                "conversation_count": session_score.conversation_count
            }
            
        except Exception as e:
            print(f"Final evaluation error: {e}")
            final_evaluation = {
                "overall_score": 70,
                "grade": "B-",
                "percentage": 70.0,
                "summary_feedback": "Good practice session! Keep working on your solar sales skills.",
                "strengths": ["Engaged in conversation"],
                "areas_for_improvement": ["Continue practicing"],
                "tips": ["Keep practicing with different personality types"],
                "conversation_count": len(self._get_conversation_history(session_id))
            }
        
        # Clean up session
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Update database with final score
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE ai_practice_sessions 
                SET status = 'completed', final_score = ?, end_time = ?
                WHERE session_id = ?
            ''', (final_evaluation.get('overall_score', 0), datetime.now().isoformat(), session_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error updating session: {e}")
        
        return final_evaluation
    
    def _generate_personality_tips(self, personality_type: str, session_score: SessionScore) -> List[str]:
        """Generate personality-specific tips"""
        tips = []
        
        if personality_type == "owl":
            tips = [
                "Provide detailed technical specifications",
                "Show efficiency data and performance studies",
                "Be patient with analytical questions",
                "Use charts and comparison tables"
            ]
        elif personality_type == "bull":
            tips = [
                "Lead with ROI and savings numbers",
                "Be direct and confident",
                "Focus on immediate benefits",
                "Avoid lengthy technical explanations"
            ]
        elif personality_type == "sheep":
            tips = [
                "Take the lead in conversations",
                "Provide clear recommendations",
                "Build trust through reassurance",
                "Simplify complex decisions"
            ]
        elif personality_type == "tiger":
            tips = [
                "Demonstrate premium expertise",
                "Position high-end solutions",
                "Match their executive style",
                "Showcase exclusive options"
            ]
        
        if session_score.overall_score < 70:
            tips.append("Continue practicing to improve your skills")
        
        return tips[:5]
    
    def generate_response(self, session_id: str, system_prompt: str, user_message: str) -> str:
        """Public method to generate AI response with custom system prompt for niche-based sessions"""
        try:
            # Build messages for OpenAI with custom system prompt
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Call OpenAI using the instance client
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            return ai_response
            
        except Exception as e:
            print(f"DEBUG: OpenAI error in generate_response: {e}")
            return "I'm having technical difficulties. Could you try again?"
    
    async def generate_response_async(self, session_id: str, system_prompt: str, user_message: str) -> str:
        """Async version of generate_response for compatibility with async code"""
        return self.generate_response(session_id, system_prompt, user_message) 

    def _restore_active_sessions(self):
        """Restore active sessions from database on startup"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            
            # First, clean up stale sessions (older than 24 hours)
            cursor.execute('''
                UPDATE ai_practice_sessions 
                SET status = 'expired', end_time = CURRENT_TIMESTAMP
                WHERE status = 'active' 
                AND datetime(start_time) < datetime('now', '-24 hours')
            ''')
            
            # Get all active sessions from database
            cursor.execute('''
                SELECT session_id, user_id, personality_type
                FROM ai_practice_sessions
                WHERE status = 'active' AND end_time IS NULL
            ''')
            
            rows = cursor.fetchall()
            conn.commit()
            conn.close()
            
            # Restore each active session
            for session_id, user_id, personality_type in rows:
                try:
                    # Get personality instance
                    personality = get_personality(personality_type)
                    
                    # Restore to active sessions
                    self.active_sessions[session_id] = {
                        "personality": personality, 
                        "user_id": user_id
                    }
                    
                    print(f"DEBUG: Restored session {session_id} for user {user_id} with personality {personality_type}")
                except Exception as e:
                    print(f"ERROR: Failed to restore session {session_id}: {e}")
                    
            print(f"DEBUG: Successfully restored {len(self.active_sessions)} active sessions from database")
            
        except sqlite3.Error as e:
            print(f"Database error restoring sessions: {e}")
            # Don't raise here, just log - bot can continue without restored sessions 

    def _attempt_session_restore(self, session_id: str) -> bool:
        """Attempt to restore a single session from database"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            
            # Check if session exists in database and is active
            cursor.execute('''
                SELECT user_id, personality_type
                FROM ai_practice_sessions
                WHERE session_id = ? AND status = 'active' AND end_time IS NULL
            ''', (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                user_id, personality_type = row
                
                # Get personality instance
                personality = get_personality(personality_type)
                
                # Restore to active sessions
                self.active_sessions[session_id] = {
                    "personality": personality, 
                    "user_id": user_id
                }
                
                print(f"DEBUG: Successfully restored session {session_id} on-demand")
                return True
            else:
                print(f"DEBUG: Session {session_id} not found in database or not active")
                return False
                
        except Exception as e:
            print(f"ERROR: Failed to restore session {session_id}: {e}")
            return False 