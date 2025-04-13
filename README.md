# Portia AI Day Planner

A GUI application that uses Portia AI to help plan and schedule events in your calendar.
Youtube Video: https://www.youtube.com/watch?v=QrKxAyH70L0&ab_channel=Ethan

## Features

- Create and manage day plans with natural language input
- Voice recognition for hands-free event entry
- AI-powered scheduling that optimizes your day
- Interactive plan review and modification
- Google Calendar integration
- Clarification system for resolving ambiguities

## Installation

1. Clone the repository:
    ```
    git clone https://github.com/yourusername/Portia_AI_Project.git
    cd Portia_AI_Project
    ```

2. Install required dependencies:
    ```
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the project root directory with your API keys (for OpenAI GPT-4o)

## Usage

1. Run the application:
    ```
    python main.py
    ```

2. Enter the day you want to plan in the "Enter day" field e.g "14th" or "20th of May"
3. Explain every event you want to do that day. It's important you specify a time and duration of every event. e.g. "Swimming at 9am for 1 hour" or "Cycling for 30 minutes finishing at 3pm"
4. Click "Generate Plan" to create your schedule
5. Review the generated plan and either accept it or provide feedback for modifications
6. After accepting, your day will be collectively structured on your Google Calendar

## Requirements

- Python 3.7+
- tkinter
- SpeechRecognition
- Portia AI framework
- Google API credentials (for calendar access)


Made for the AI Encode Hackathon
