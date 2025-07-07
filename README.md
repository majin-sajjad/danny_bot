# 🤖 Danny Bot - The AI-Powered Sales Training Platform

Danny Bot is a sophisticated, AI-powered Discord bot that transforms your server into a dynamic sales training environment. It provides a structured platform for users to practice sales skills, receive coaching, track their performance, and compete on leaderboards, all driven by advanced AI conversation partners.

## 🌟 Key Features

*   **🤖 AI-Powered Role-Playing:** Practice sales conversations with 4 built-in, psychologically-profiled customer personalities (Analytical, Aggressive, Passive, Dominant).
*   **🛠️ Custom AI Creation:** Design and build your own custom AI customer personalities in the Playground for limitless, tailored training scenarios.
*   **🔒 Private & Personalized Training Zones:** Every user receives a private 5-channel category for focused, confidential practice and coaching.
*   **🏆 Deals & Leaderboard System:** Submit sales "deals" through a UI-based form, earn points, and compete on weekly, monthly, and all-time leaderboards.
*   **📊 Performance Scoring & Analytics:** Receive real-time, personality-specific scores on your practice sessions and track your long-term progress with detailed statistics.
*   **👨‍💼 Comprehensive Admin Suite:** Powerful admin commands for server setup, user management, diagnostics, and maintenance.
*   **🎨 Intuitive UI:** A clean, modern interface that relies on Discord's native buttons and modals for an easy-to-use experience.

## 🚀 Getting Started

Follow these steps to get Danny Bot up and running on your server.

### 1. Prerequisites

*   Python 3.8+
*   A Discord Bot Token with **Message Content**, **Server Members**, and **Presence** intents enabled.
*   An OpenAI API Key.
*   Git installed on your system.

### 2. Installation & Configuration

```bash
# 1. Clone the repository
git clone <your-repository-url>
cd danny-pessy-bot

# 2. Install the required dependencies
pip install -r requirements.txt

# 3. Create and configure your environment file
# (This file stores your secret keys)
# On Windows:
copy .\docs\setup\env_template.txt .env

# On macOS/Linux:
# cp docs/setup/env_template.txt .env

# 4. Edit the .env file with your credentials
# Open the new .env file and paste in your actual tokens and keys.
# DISCORD_BOT_TOKEN=your_discord_bot_token_here
# OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Running the Bot

Once configured, you can start the bot with a single command:

```bash
python main.py
```

You should see a confirmation in your terminal that the bot has connected to Discord successfully.

### 4. Initial Server Setup (Admin Only)

To create the entire server infrastructure, including all the necessary channels, roles, and welcome messages, run the following command in any channel:

```
!admin_setup_server
```

The bot will build everything out automatically.

### 5. Your First User

New users join the server and go to the `#🎯welcome-start-here` channel.

1.  Click the **"🚀 Get Started"** button.
2.  The bot will instantly create a private category named **"🔒 [Username]'s Training Zone"**.
3.  This private zone contains the 5 channels needed for training and is only visible to that user and server admins.

## 📖 How to Use Danny Bot

### The Private Training Zone

Each user's private zone contains five specialized channels:

*   **💪practice-arena:** The primary channel for role-playing with the built-in AI personalities.
*   **🛠️playground-lab:** Where you can create, manage, and test your own custom AI personalities.
*   **🤖personal-assistant:** A dedicated space for your personal AI sales coach (feature in development).
*   **📊my-progress:** View your detailed statistics, scores, achievements, and track your improvement.
*   **📚my-library:** A place to store your saved custom personalities and review past practice sessions.

### Practicing with an AI

1.  Navigate to your private **#💪practice-arena** channel.
2.  Use the buttons to see the list of available AI personalities or to start a new session.
3.  Choose a personality (e.g., 🦉 **Owl**). The AI will start the conversation with a characteristic opening line.
4.  Engage in a natural, back-and-forth sales conversation.
5.  When you're finished, click the "End Session" button to receive a detailed performance score.

### Submitting Deals & Climbing the Leaderboard

1.  Go to your private **#deal-submission** channel (often located within a "Community" or "Sales" category created during setup).
2.  Click the **"Submit New Deal"** button.
3.  Fill out the modal form with the deal details (e.g., Setter, Closer, Self-Generated).
4.  Once your deal is approved by an admin, you'll be awarded points.
5.  Track your standing on the server leaderboards!

## ⚙️ Command Reference

While most user interaction is through UI buttons, some text commands are available.

### User Commands

*   `!help`: Displays a comprehensive guide to the bot's features and commands.
*   `!leaderboard`: Shows the current leaderboard rankings.
*   `!mystats`: Displays your personal performance statistics.
*   `!profile`: Shows your complete user profile, including achievements and progress.

### Admin Commands (Prefix: `!admin_`)

*   `!admin_setup_server`: (Owner Only) Creates the entire server channel and role infrastructure.
*   `!admin_reset_server`: (Owner Only) Wipes and rebuilds the server structure.
*   `!admin_dashboard`: Opens an administrative control panel.
*   `!admin_user_info @user`: Retrieves detailed information about a specific user.
*   `!admin_add_deal @user ...`: Manually adds a deal for a user.
*   `!admin_fix_all_training_zones`: A powerful server-wide diagnostic and repair tool for all training zones.
*   `!diagnose_issues @user`: Runs a diagnostic check for an individual user's training zone.
*   `!admin_help`: Shows a complete list of administrative commands.

## 🛠️ Technical Overview

### Architecture

The bot is built with a modular architecture to ensure scalability and maintainability.

*   **`core/`**: Contains the main bot logic, database manager, and event handlers.
*   **`systems/`**: Houses the major independent features like Leaderboards, Playground, and Registration.
*   **`ai/`**: Manages all AI integration, including personality definitions, response generation, and memory.
*   **`ui/`**: Defines all user-facing components, such as Buttons, Modals, and Views.
*   **`commands/`**: Separates admin and user command logic.
*   **`database`**: A local `danny_bot.db` SQLite file is created to store all persistent data.

### Database Schema

The bot uses an SQLite database (`danny_bot.db`) to store all data, including:

*   `user_registrations`: User account data, preferences, and niche.
*   `practice_sessions`: History and scores of all training sessions.
*   `deals`: All submitted deals, their status, and awarded points.
*   `custom_personalities`: All user-created AI personalities.
*   `leaderboard_snapshots`: Historical leaderboard data for tracking progress.

## 📈 Project Status & Roadmap

This project has undergone several phases of cleanup, standardization, and feature development. It is considered **stable and production-ready**.

### Future Enhancements

While the core system is complete, future development could include:
*   **Advanced Gamification:** More achievements, badges, and rewards.
*   **CRM Integration:** Connect deal submissions to external sales tools.
*   **Team Features:** Allow managers to review team performance and create private team training scenarios.
*   **Voice Channel Integration:** Enable live voice-based practice sessions with the AI.
*   **Multi-language Support.** 