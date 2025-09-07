# 🍽️ Get More Diners - Restaurant Marketing SaaS

> **AI-powered marketing platform for US restaurant owners to find local diners, create campaigns, and send personalized offers via email and SMS.**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy)
[![Deploy on Vercel](https://vercel.com/button)](https://vercel.com/new/clone)

## ✨ **Features**

- 🔐 **User Authentication** - Secure signup/login with Supabase
- 🏪 **Restaurant Profiles** - Create and manage restaurant information
- 🔍 **Smart Customer Search** - Find diners by location, interests, and preferences
- 🤖 **AI Content Generation** - Create compelling email/SMS campaigns with AI
- 📧 **Campaign Management** - Send personalized offers to targeted audiences
- 📊 **Campaign Analytics** - Track sent campaigns and performance
- 📱 **Responsive Design** - Works perfectly on desktop and mobile

## 🚀 **Quick Start**

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account
- OpenAI API key (optional)

### 1. Clone & Setup
```bash
git clone https://github.com/hamidreza23/Get-More-Diners.git
cd Get-More-Diners
```

### 2. Database Setup
1. Create a [Supabase](https://supabase.com) project
2. Go to SQL Editor and run `supabase/schema.sql`
3. Copy your project URL and API keys

### 3. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env
# Edit .env with your Supabase credentials
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup
```bash
cd frontend
npm install
cp env.local.example .env.local
# Edit .env.local with your Supabase credentials
npm run dev
```

### 5. Access
- **App**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 🛠️ **Tech Stack**

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: Supabase PostgreSQL
- **AI**: OpenAI GPT-4o-mini
- **Auth**: Supabase Auth

## 📁 **Project Structure**

```
Get-More-Diners/
├── frontend/          # Next.js app
├── backend/           # FastAPI server
├── supabase/          # Database schema
└── README.md
```

## 🚀 **Deployment**

### Option 1: Vercel + Railway (Recommended)

**Frontend (Vercel):**
1. Connect GitHub repo to [Vercel](https://vercel.com)
2. Set root directory to `frontend`
3. Add environment variables

**Backend (Railway):**
1. Connect GitHub repo to [Railway](https://railway.app)
2. Set root directory to `backend`
3. Add PostgreSQL database
4. Add environment variables

### Option 2: All-in-One Railway

1. Connect GitHub repo to [Railway](https://railway.app)
2. Add PostgreSQL database
3. Set environment variables for both frontend and backend

## 🔧 **Environment Variables**

### Backend (.env)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key
DATABASE_URL=postgresql+asyncpg://...
JWT_JWKS_URL=https://your-project.supabase.co/auth/v1/keys
OPENAI_API_KEY=sk-... # Optional
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

## 📊 **Demo Data**

The app includes a sample dataset of 99 diners across various US cities with different interests and preferences. Perfect for testing the search and campaign features!

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 **License**

MIT License - see LICENSE file for details

---

**Built with ❤️ for restaurant owners** - Transform your marketing with AI-powered customer targeting and personalized campaigns.
