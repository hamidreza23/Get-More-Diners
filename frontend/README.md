# Frontend App

Next.js frontend for Get More Diners restaurant marketing platform.

## Quick Start

```bash
npm install
cp env.local.example .env.local
# Edit .env.local with your credentials
npm run dev
```

## Environment Variables

Copy `env.local.example` to `.env.local` and configure:

- `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Features

- 🔐 User authentication
- 🏪 Restaurant profile management
- 🔍 Customer search with filters
- 📧 Campaign creation with AI
- 📊 Campaign analytics
- 📱 Responsive design

## Tech Stack

- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Supabase Auth
