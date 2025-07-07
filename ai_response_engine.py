"""
AI Response Engine for Danny Bot
===============================

This module handles:
- Integration with OpenAI API
- Personality-driven conversations
- Session management and context
- Scoring and evaluation
- Vector database integration for memory
"""

import openai
import os
import asyncio
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
from dataclasses import dataclass
from openai import OpenAI

from ai_personalities import get_personality, get_available_personalities
from vector_memory_manager import VectorMemoryManager
from scoring_system import SolarSalesScorer, SessionScore

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI client (new format)
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@dataclass
class PracticeSession:
    """Data class for practice sessions"""
    session_id: str
    user_id: str
    personality_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    score: Optional[int] = None
    feedback: Optional[str] = None
    conversation_count: int = 0
    status: str = "active"  # active, completed, paused

class AIResponseEngine:
    """Main AI response engine for Danny Bot"""
    
    def __init__(self, db_path: str = "danny_bot.db"):
        self.db_path = db_path
        self.vector_manager = VectorMemoryManager()
        self.active_sessions: Dict[str, PracticeSession] = {}
        self.personality_instances: Dict[str, object] = {}
        self.scorer = SolarSalesScorer()
        
        # Initialize database
        self._init_database()
        # 🔧 NEW: Restore active sessions from database on startup
        self._restore_active_sessions()
    
    def _init_database(self):
        """Initialize the database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Practice sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS practice_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                personality_type TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                score INTEGER,
                feedback TEXT,
                conversation_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Conversation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                message_type TEXT NOT NULL, -- 'user' or 'ai'
                message_content TEXT NOT NULL,
                personality_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES practice_sessions (session_id)
            )
        ''')
        
        # Practice scores table (detailed scoring)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS practice_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                personality_type TEXT NOT NULL,
                score_category TEXT NOT NULL,
                score_value INTEGER NOT NULL,
                max_score INTEGER NOT NULL,
                notes TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES practice_sessions (session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _restore_active_sessions(self):
        """Restore active sessions from database on startup"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First, clean up stale sessions (older than 24 hours)
            cursor.execute('''
                UPDATE practice_sessions 
                SET end_time = CURRENT_TIMESTAMP
                WHERE end_time IS NULL 
                AND datetime(start_time) < datetime('now', '-24 hours')
            ''')
            
            # Get all active sessions from database (using the correct table)
            cursor.execute('''
                SELECT session_id, user_id, personality_type, start_time, 0 as conversation_count
                FROM practice_sessions
                WHERE end_time IS NULL
            ''')
            
            rows = cursor.fetchall()
            conn.commit()
            conn.close()
            
            # Restore each active session
            for session_id, user_id, personality_type, start_time, conversation_count in rows:
                try:
                    # Create PracticeSession object
                    session = PracticeSession(
                        session_id=session_id,
                        user_id=user_id,
                        personality_type=personality_type,
                        start_time=datetime.fromisoformat(start_time) if isinstance(start_time, str) else start_time,
                        conversation_count=conversation_count or 0,
                        status="active"
                    )
                    
                    # Get personality instance
                    personality = get_personality(personality_type)
                    
                    # Restore to active sessions
                    self.active_sessions[session_id] = session
                    self.personality_instances[session_id] = personality
                    
                    print(f"DEBUG: Restored session {session_id} for user {user_id} with personality {personality_type}")
                except Exception as e:
                    print(f"ERROR: Failed to restore session {session_id}: {e}")
                    
            print(f"DEBUG: Successfully restored {len(self.active_sessions)} active sessions from database")
            
        except sqlite3.Error as e:
            print(f"Database error restoring sessions: {e}")
            # Don't raise here, just log - bot can continue without restored sessions
    
    async def start_practice_session(self, user_id: str, personality_type: str, context: str = "") -> Tuple[str, str]:
        """
        Start a new practice session
        Returns: (session_id, opening_message)
        """
        # Validate personality type
        if personality_type not in get_available_personalities():
            raise ValueError(f"Invalid personality type: {personality_type}")
        
        # Create session ID
        session_id = f"{user_id}_{personality_type}_{int(datetime.now().timestamp())}"
        
        # Create practice session
        session = PracticeSession(
            session_id=session_id,
            user_id=user_id,
            personality_type=personality_type,
            start_time=datetime.now()
        )
        
        # Store in active sessions
        self.active_sessions[session_id] = session
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO practice_sessions 
            (session_id, user_id, personality_type, start_time, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, personality_type, session.start_time, "active"))
        conn.commit()
        conn.close()
        
        # Get personality instance
        personality = get_personality(personality_type)
        self.personality_instances[session_id] = personality
        
        # Add context if provided
        if context:
            personality.add_context("user_context", context)
        
        # Generate opening message
        opening_message = await self._generate_opening_message(personality, user_id, context)
        
        # Store the opening message
        await self._store_conversation(session_id, user_id, "ai", opening_message, personality_type)
        
        return session_id, opening_message
    
    async def continue_conversation(self, session_id: str, user_message: str) -> Tuple[str, Optional[Dict]]:
        """
        Continue an existing conversation
        Returns: (ai_response, scoring_data_if_applicable)
        """
        # 🔧 NEW: If session not in active sessions, try to restore it from database
        if session_id not in self.active_sessions:
            print(f"DEBUG: Session {session_id} not found in active_sessions, attempting to restore...")
            if not await self._attempt_session_restore(session_id):
                print(f"DEBUG: Failed to restore session {session_id}")
                raise ValueError(f"Session {session_id} not found or expired")
        
        session = self.active_sessions[session_id]
        personality = self.personality_instances[session_id]
        
        # Store user message
        await self._store_conversation(session_id, session.user_id, "user", user_message, session.personality_type)
        
        # Get conversation history for context
        conversation_history = await self._get_conversation_history(session_id, limit=10)
        
        # Generate AI response
        ai_response = await self._generate_ai_response(
            personality, 
            user_message, 
            conversation_history,
            session.user_id
        )
        
        # Store AI response
        await self._store_conversation(session_id, session.user_id, "ai", ai_response, session.personality_type)
        
        # Update conversation count
        session.conversation_count += 1
        await self._update_session_conversation_count(session_id, session.conversation_count)
        
        # Check if we should provide scoring (every 5 exchanges or on specific triggers)
        scoring_data = None
        if session.conversation_count >= 5 and session.conversation_count % 5 == 0:
            scoring_data = await self._evaluate_conversation(session_id, personality)
        
        return ai_response, scoring_data
    
    async def end_practice_session(self, session_id: str) -> Dict:
        """
        End a practice session and provide final scoring
        Returns: final_evaluation_data
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        personality = self.personality_instances[session_id]
        
        # Generate final evaluation
        final_evaluation = await self._generate_final_evaluation(session_id, personality)
        
        # Update session in database
        session.end_time = datetime.now()
        session.status = "completed"
        session.score = final_evaluation["overall_score"]
        session.feedback = final_evaluation["summary_feedback"]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE practice_sessions 
            SET end_time = ?, status = ?, score = ?, feedback = ?
            WHERE session_id = ?
        ''', (session.end_time, session.status, session.score, session.feedback, session_id))
        conn.commit()
        conn.close()
        
        # Store detailed scores
        await self._store_detailed_scores(session_id, final_evaluation["detailed_scores"])
        
        # Clean up active session
        del self.active_sessions[session_id]
        del self.personality_instances[session_id]
        
        return final_evaluation
    
    async def _generate_opening_message(self, personality, user_id: str, context: str) -> str:
        """Generate the opening message for a practice session"""
        
        # Get a conversation starter from the personality
        starter = personality.conversation_starters[0]  # Could randomize this
        
        # Use OpenAI to make it more natural and contextual
        system_prompt = personality.get_system_prompt(context)
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please start our sales training conversation. Be natural and engaging. Here's a conversation starter you could use or adapt: '{starter}'"}
                ],
                max_tokens=150,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to basic starter
            return starter
    
    async def _generate_ai_response(self, personality, user_message: str, conversation_history: List, user_id: str) -> str:
        """Generate AI response using the personality"""
        
        # Build conversation context
        messages = [
            {"role": "system", "content": personality.get_system_prompt()}
        ]
        
        # Add conversation history
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            role = "assistant" if msg['message_type'] == 'ai' else "user"
            messages.append({"role": role, "content": msg['message_content']})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=300,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "I apologize, but I'm having technical difficulties. Could you please try again?"
    
    async def _evaluate_conversation(self, session_id: str, personality) -> Dict:
        """Evaluate the current conversation using the new scoring system"""
        
        # Get conversation history
        conversation_history = await self._get_conversation_history(session_id)
        
        # Convert to format expected by scorer
        formatted_history = []
        for msg in conversation_history:
            formatted_history.append({
                'message_type': msg['message_type'],
                'content': msg['message_content'],
                'timestamp': msg['timestamp']
            })
        
        # Get session info
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Use the new scoring system
        try:
            session_score: SessionScore = self.scorer.evaluate_conversation(
                personality.personality_type,
                formatted_history,
                session.user_id
            )
            
            # Convert to dictionary format for compatibility
            evaluation_data = {
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
            
            # Store detailed scores
            await self._store_session_score(session_id, session_score)
            
            return evaluation_data
            
        except Exception as e:
            print(f"Scoring error: {e}")
            # Return basic evaluation
            return {
                "overall_score": 70,
                "percentage": 70.0,
                "grade": "C+",
                "feedback": "Keep practicing! Focus on understanding your customer's personality type.",
                "strengths": ["Engaged in conversation"],
                "improvements": ["Study personality types more"],
                "conversation_count": len(formatted_history)
            }
    
    async def _generate_final_evaluation(self, session_id: str, personality) -> Dict:
        """Generate comprehensive final evaluation using the new scoring system"""
        
        # Get full conversation history
        conversation_history = await self._get_conversation_history(session_id)
        
        # Convert to format expected by scorer
        formatted_history = []
        for msg in conversation_history:
            formatted_history.append({
                'message_type': msg['message_type'],
                'content': msg['message_content'],
                'timestamp': msg['timestamp']
            })
        
        # Get session info
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        try:
            # Use the new scoring system for final evaluation
            session_score: SessionScore = self.scorer.evaluate_conversation(
                personality.personality_type,
                formatted_history,
                session.user_id
            )
            
            # Generate additional tips based on personality type
            tips = self._generate_personality_tips(personality.personality_type, session_score)
            
            # Build comprehensive final evaluation
            final_evaluation = {
                "detailed_scores": {
                    breakdown.category: breakdown.score 
                    for breakdown in session_score.breakdown
                },
                "overall_score": session_score.overall_score,
                "grade": session_score.grade,
                "percentage": session_score.percentage,
                "summary_feedback": session_score.solar_specific_feedback,
                "strengths": session_score.strengths,
                "areas_for_improvement": session_score.improvements,
                "tips": tips,
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
            
            # Store the final evaluation
            await self._store_session_score(session_id, session_score)
            
            return final_evaluation
            
        except Exception as e:
            print(f"Final evaluation error: {e}")
            # Return basic evaluation
            return {
                "detailed_scores": {"overall": 75},
                "overall_score": 75,
                "grade": "B",
                "percentage": 75.0,
                "summary_feedback": f"Good practice session with {personality.personality_type} customer!",
                "strengths": ["Engaged in conversation", "Showed persistence"],
                "areas_for_improvement": ["Study personality types more", "Practice specific techniques"],
                "tips": [f"Focus on {personality.personality_type}-specific approaches", "Keep practicing!"],
                "conversation_count": len(formatted_history)
            }
    
    async def _store_conversation(self, session_id: str, user_id: str, message_type: str, content: str, personality_type: str):
        """Store conversation message in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversation_history 
            (session_id, user_id, message_type, message_content, personality_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, message_type, content, personality_type))
        conn.commit()
        conn.close()
        
        # Also store in vector database for memory
        await self.vector_manager.store_conversation(
            user_id, f"{message_type}: {content}", 
            {"session_id": session_id, "personality_type": personality_type}
        )
    
    async def _get_conversation_history(self, session_id: str, limit: int = None) -> List[Dict]:
        """Get conversation history from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT message_type, message_content, personality_type, timestamp
            FROM conversation_history 
            WHERE session_id = ?
            ORDER BY timestamp ASC
        '''
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "message_type": row[0],
                "message_content": row[1],
                "personality_type": row[2],
                "timestamp": row[3]
            }
            for row in rows
        ]
    
    async def _update_session_conversation_count(self, session_id: str, count: int):
        """Update conversation count in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE practice_sessions 
            SET conversation_count = ?
            WHERE session_id = ?
        ''', (count, session_id))
        conn.commit()
        conn.close()
    
    async def _store_detailed_scores(self, session_id: str, scores: Dict):
        """Store detailed scoring data (legacy method)"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for category, score in scores.items():
            cursor.execute('''
                INSERT INTO practice_scores 
                (session_id, user_id, personality_type, score_category, score_value, max_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, session.user_id, session.personality_type, category, score, 100))
        
        conn.commit()
        conn.close()
    
    async def _store_session_score(self, session_id: str, session_score: SessionScore):
        """Store comprehensive session score using new scoring system"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update the main session with overall score
        cursor.execute('''
            UPDATE practice_sessions 
            SET score = ?, feedback = ?, end_time = CURRENT_TIMESTAMP, status = 'completed'
            WHERE session_id = ?
        ''', (session_score.overall_score, session_score.solar_specific_feedback, session_id))
        
        # Store detailed breakdown scores
        for breakdown in session_score.breakdown:
            cursor.execute('''
                INSERT INTO practice_scores 
                (session_id, user_id, personality_type, score_category, score_value, max_score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, 
                session.user_id, 
                session.personality_type, 
                breakdown.category, 
                breakdown.score, 
                breakdown.max_score,
                breakdown.feedback
            ))
        
        conn.commit()
        conn.close()
        
        # Update active session
        session.score = session_score.overall_score
        session.feedback = session_score.solar_specific_feedback
        session.status = "completed"
    
    def _generate_personality_tips(self, personality_type: str, session_score: SessionScore) -> List[str]:
        """Generate personality-specific tips based on performance"""
        tips = []
        
        if personality_type == "owl":
            tips = [
                "Always provide specific data and technical details",
                "Be patient with analytical questions",
                "Use charts, graphs, and performance studies",
                "Explain warranties and system specifications thoroughly",
                "Provide multiple options with detailed comparisons"
            ]
            if session_score.overall_score < 70:
                tips.extend([
                    "Study solar efficiency ratings and performance data",
                    "Practice explaining technical concepts clearly",
                    "Prepare case studies and customer examples"
                ])
        
        elif personality_type == "bull":
            tips = [
                "Lead with bottom-line savings and ROI",
                "Be direct and confident in your communication",
                "Focus on immediate benefits and quick payback",
                "Don't get bogged down in technical details",
                "Present strong value propositions"
            ]
            if session_score.overall_score < 70:
                tips.extend([
                    "Practice calculating specific monthly savings",
                    "Develop confident closing techniques",
                    "Focus on competitive advantages"
                ])
        
        elif personality_type == "sheep":
            tips = [
                "Take the lead and provide clear guidance",
                "Build trust through reassurance and support",
                "Simplify complex decisions into clear options",
                "Share testimonials and neighbor references",
                "Provide step-by-step process explanations"
            ]
            if session_score.overall_score < 70:
                tips.extend([
                    "Practice consultative selling techniques",
                    "Develop trust-building conversation starters",
                    "Prepare customer success stories"
                ])
        
        elif personality_type == "tiger":
            tips = [
                "Demonstrate premium expertise and credentials",
                "Position yourself as the top solar professional",
                "Showcase high-end products and services",
                "Match their executive communication style",
                "Provide exclusive or premium options"
            ]
            if session_score.overall_score < 70:
                tips.extend([
                    "Study premium solar brands and technologies",
                    "Practice executive-level communication",
                    "Develop premium service propositions"
                ])
        
        return tips[:7]  # Limit to 7 tips
    
    async def get_user_practice_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get user's practice session history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, personality_type, start_time, end_time, score, conversation_count, status
            FROM practice_sessions 
            WHERE user_id = ?
            ORDER BY start_time DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "session_id": row[0],
                "personality_type": row[1],
                "start_time": row[2],
                "end_time": row[3],
                "score": row[4],
                "conversation_count": row[5],
                "status": row[6]
            }
            for row in rows
        ]
    
    async def get_personality_stats(self, user_id: str) -> Dict:
        """Get user's performance stats by personality type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                personality_type,
                COUNT(*) as session_count,
                AVG(score) as avg_score,
                MAX(score) as best_score,
                SUM(conversation_count) as total_conversations
            FROM practice_sessions 
            WHERE user_id = ? AND status = 'completed'
            GROUP BY personality_type
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = {}
        for row in rows:
            stats[row[0]] = {
                "session_count": row[1],
                "average_score": round(row[2], 1) if row[2] else 0,
                "best_score": row[3] or 0,
                "total_conversations": row[4] or 0
            }
        
        return stats 

    async def generate_response(self, system_prompt: str, user_message: str, max_tokens: int = 300) -> str:
        """Generate AI response with custom system prompt (for compatibility with TrainingZoneManager)"""
        try:
            # Build messages for OpenAI with custom system prompt
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Call OpenAI using the openai_client (synchronous call, no await)
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,  # Use the parameter passed in
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content.strip()
            finish_reason = response.choices[0].finish_reason
            
            # Debug logging to see what's happening
            print(f"DEBUG: AI response length: {len(ai_response)} characters")
            print(f"DEBUG: Finish reason: {finish_reason}")
            print(f"DEBUG: AI response preview: {ai_response[:100]}...")
            if len(ai_response) > 100:
                print(f"DEBUG: AI response ending: ...{ai_response[-100:]}")
            
            # Check if response was truncated
            if finish_reason == "length":
                print("WARNING: AI response was truncated due to token limit!")
            
            return ai_response
            
        except Exception as e:
            print(f"OpenAI error in generate_response: {e}")
            return "I'm having technical difficulties. Could you try again?" 

    async def _attempt_session_restore(self, session_id: str) -> bool:
        """Attempt to restore a single session from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if session exists in database and is active
            cursor.execute('''
                SELECT user_id, personality_type, start_time, 0 as conversation_count
                FROM practice_sessions
                WHERE session_id = ? AND end_time IS NULL
            ''', (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                user_id, personality_type, start_time, conversation_count = row
                
                # Create PracticeSession object
                session = PracticeSession(
                    session_id=session_id,
                    user_id=user_id,
                    personality_type=personality_type,
                    start_time=datetime.fromisoformat(start_time) if isinstance(start_time, str) else start_time,
                    conversation_count=conversation_count or 0,
                    status="active"
                )
                
                # Get personality instance
                personality = get_personality(personality_type)
                
                # Restore to active sessions
                self.active_sessions[session_id] = session
                self.personality_instances[session_id] = personality
                
                print(f"DEBUG: Successfully restored session {session_id} on-demand")
                return True
            else:
                print(f"DEBUG: Session {session_id} not found in database or not active")
                return False
                
        except Exception as e:
            print(f"ERROR: Failed to restore session {session_id}: {e}")
            return False 