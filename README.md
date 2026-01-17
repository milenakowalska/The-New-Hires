# The New Hires

**An AI-Powered Team Onboarding Simulation**

*Google Great AI Hackathon Project*

## Overview

The New Hires is an innovative web application that simulates a compressed team onboarding experience, allowing new employees to experience a full 30-day onboarding cycle in just 7 days. The platform creates an immersive environment with realistic team interactions, scheduled meetings, daily standups, and sprint cycles—all powered by AI to provide an authentic workplace experience.

## Features

### 🚀 Compressed Sprint Simulation
- Experience a 30-day onboarding cycle compressed into 7 days
- Two-week sprint condensed into one week for rapid learning
- Time-accelerated workflow to maximize learning efficiency

### 💬 Interactive Communication
- Simulated Slack messages for realistic team communication
- Daily standup meetings with AI-generated team interactions
- Real-time notifications and updates

### ✅ Structured Onboarding Journey
- Comprehensive checklists for tracking progress
- Milestone-based learning paths
- Task management and completion tracking

### 🎤 Mock Meetings & Audio Integration
- Simulated team meetings with AI participants
- Audio integration using OpenAI TTS for realistic voice synthesis
- Realistic meeting scenarios including planning sessions and retrospectives

### 📊 Performance Dashboard & Retrospective
- Comprehensive performance dashboard tracking your progress
- Structured feedback areas for "What went well" reflections
- "What could improve" section for constructive feedback
- Complete retrospective at the end of your onboarding journey

## Tech Stack

### Backend
- **PostgreSQL**: Local database (`the_new_hire` with `postgres:postgres` credentials)
- **Python**: Backend API development
- **Flask/FastAPI**: API framework

### Frontend
- **React.js**: Modern UI framework
- **TypeScript**: Type-safe development

### APIs & Services
- **Google AI Studio (Gemini)**: Core AI capabilities for meeting simulation, workflow automation, and text-to-speech (TTS) fallback
- **GitHub API**: Integration for developer workflows
- **Supabase**: Backend authentication and data management

### Tools
- **Antigravity**: Project scaffolding
- **Lovable**: Project development platform with GitHub OAuth integration

## Installation

### Prerequisites
- Node.js (v16+)
- Python (v3.8+)
- PostgreSQL
- API keys for Google AI Studio (Gemini) and GitHub

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/UtsahaJoshi/The-New-Hires.git
cd The-New-Hires
```

2. **Set up PostgreSQL database**

```bash
psql -U postgres
CREATE DATABASE the_new_hire;
```

3. **Configure environment variables**

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost/the_new_hire
GOOGLE_AI_API_KEY=your_google_ai_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

4. **Install backend dependencies**

```bash
cd backend
pip install -r requirements.txt
```

5. **Install frontend dependencies**

```bash
cd frontend
npm install
```

6. **Run Alembic database migrations**

Make sure you're inside the `backend` directory and that your `.env` file is correctly configured before running migrations.

```bash
cd backend
alembic upgrade head
```

✅ This will:

* Create all required database tables
* Apply the correct schemas
* Ensure your database is in sync with the latest backend models

If you ever need to reset migrations:

```bash
alembic downgrade base
alembic upgrade head
```

7. **Start the development servers**

Backend:

```bash
uvicorn main:app --reload
```

#### Frontend:

```bash
npm run dev
```

## Running Tests Locally

### Backend Tests
Ensure you are in the `backend` directory and have your virtual environment activated:

```bash
cd backend
pytest
```

### Frontend Tests
Ensure you are in the `frontend` directory:

```bash
cd frontend
npm test
```



## Usage

1. **Sign up/Login** using GitHub OAuth
2. **Start your onboarding journey** by selecting a simulated role
3. **Complete daily tasks** and checklists
4. **Attend mock meetings** with AI-generated teammates
5. **Participate in standups** and sprint planning sessions
6. **Review your performance dashboard** to track progress
7. **Complete the retrospective** with structured feedback on what went well and areas for improvement

## Project Structure

```
The-New-Hires/
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   └── app.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.tsx
│   └── package.json
├── database/
│   └── migrations/
├── .env.example
└── README.md
```

## Team

- **Arnab Mandol**
- **Milena Kowalska**
- **Nikolaus Weingartmair**
- **Gaurav Parajuli**
- **Utsaha Joshi**

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project was developed for the Google Great AI Hackathon.

## Contact

- GitHub: [@UtsahaJoshi](https://github.com/UtsahaJoshi)

## Acknowledgments

- Google for providing powerful AI capabilities via Gemini
- The open-source community for inspiration and tools

***

*Built with ❤️ for the Google Great AI Hackathon*