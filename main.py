import os
import logging
import asyncio
import sys
from dotenv import load_dotenv
from core.bot import DannyBot

# Load environment variables
load_dotenv()

# Configure logging with proper Unicode handling for Windows
class SafeStreamHandler(logging.StreamHandler):
    """Stream handler that safely handles Unicode characters"""
    
    def __init__(self, stream=None):
        super().__init__(stream)
        # Force UTF-8 encoding for Windows console
        if hasattr(self.stream, 'reconfigure'):
            try:
                self.stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass  # If reconfigure fails, continue with default
    
    def emit(self, record):
        try:
            # Try normal emit first
            super().emit(record)
        except UnicodeEncodeError:
            # If Unicode error occurs, strip non-ASCII characters
            try:
                msg = self.format(record)
                # Replace problematic Unicode characters
                safe_msg = msg.encode('ascii', 'replace').decode('ascii')
                if hasattr(self.stream, 'write'):
                    self.stream.write(safe_msg + self.terminator)
                    self.stream.flush()
            except Exception:
                # Last resort: skip the problematic log entry
                pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('danny_bot.log', encoding='utf-8'),
        SafeStreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main bot entry point"""
    try:
        # Get bot token (try both BOT_TOKEN and DISCORD_BOT_TOKEN)
        bot_token = os.getenv('BOT_TOKEN') or os.getenv('DISCORD_BOT_TOKEN')
        if not bot_token:
            logger.error("BOT_TOKEN or DISCORD_BOT_TOKEN not found in environment variables")
            return
        
        # Create and run bot
        bot = DannyBot()
        
        # Start the bot
        async with bot:
            await bot.start(bot_token)
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 