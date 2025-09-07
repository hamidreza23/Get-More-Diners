# Backend API

FastAPI backend for Get More Diners restaurant marketing platform.

## Quick Start

```bash
pip install -r requirements.txt
cp env.example .env
# Edit .env with your credentials
uvicorn app.main:app --reload --port 8000
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Environment Variables

Copy `env.example` to `.env` and configure:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key (optional)

## Features

- 🔐 JWT Authentication with Supabase
- 🏪 Restaurant management
- 👥 Customer search and filtering
- 📧 Campaign creation and management
- 🤖 AI-powered content generation
- 📊 Campaign analytics
