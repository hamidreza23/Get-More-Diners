# Supabase Database Setup

This directory contains the database schema and configuration for the Restaurant SaaS platform.

## 🗄️ Database Schema

The schema includes the following main tables:

- **restaurants** - Restaurant information and ownership
- **diners** - Customer database for marketing campaigns  
- **campaigns** - Marketing campaigns created by restaurant owners
- **campaign_recipients** - Tracking of campaign delivery and recipients

## 🚀 Setup Instructions

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up/sign in to your account
3. Click "New Project"
4. Choose your organization
5. Fill in project details:
   - Name: `restaurant-saas`
   - Database Password: (choose a strong password)
   - Region: (select closest to your users)
6. Click "Create new project"

### 2. Run the Database Schema

1. **Open SQL Editor**
   - In your Supabase dashboard, navigate to the **SQL Editor** tab
   - This is where you'll execute the schema creation script

2. **Copy and Execute Schema**
   - Open the `schema.sql` file in this directory
   - Copy the entire contents of the file
   - Paste it into the SQL Editor
   - Click **"Run"** to execute the schema

3. **Verify Tables Created**
   - Navigate to the **Table Editor** tab
   - You should see the following tables:
     - `restaurants`
     - `diners` 
     - `campaigns`
     - `campaign_recipients`

### 3. Configure Environment Variables

After setting up the database, you'll need these values for your application:

```bash
# Get these from: Settings → API → Project URL
SUPABASE_URL=https://your-project-id.supabase.co

# Get these from: Settings → API → Project API keys
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 4. Enable Row Level Security (RLS)

The schema automatically enables RLS and creates policies for:

- **Restaurant Isolation**: Users can only access their own restaurants
- **Campaign Security**: Users can only view/create campaigns for their restaurants  
- **Recipient Privacy**: Campaign recipients are only visible to campaign owners

### 5. Test the Setup

You can test the setup by:

1. **Creating a test user** via Supabase Auth
2. **Inserting a restaurant** record with the user's ID
3. **Verifying RLS policies** work correctly

Example test queries:

```sql
-- Insert a test restaurant (replace user_id with actual auth.users.id)
INSERT INTO public.restaurants (owner_user_id, name, cuisine, city, state)
VALUES ('your-user-id', 'Test Restaurant', 'Italian', 'San Francisco', 'CA');

-- Insert test diners
INSERT INTO public.diners (first_name, last_name, email, city, interests)
VALUES 
  ('John', 'Doe', 'john@example.com', 'San Francisco', ARRAY['fine_dining']),
  ('Jane', 'Smith', 'jane@example.com', 'Oakland', ARRAY['casual_dining', 'coffee_shops']);
```

## 📋 Schema Features

### Extensions Enabled
- **uuid-ossp**: UUID generation
- **pg_trgm**: Trigram matching for fuzzy text search
- **btree_gin**: GIN indexes for better performance

### Indexes Created
- City and state indexes on diners for location-based queries
- GIN index on interests array for efficient array searches
- Trigram index on city for fuzzy matching

### Row Level Security
- Multi-tenant isolation ensuring users only see their own data
- Secure campaign and recipient access through ownership chains
- Automatic enforcement at the database level

## 🔧 Maintenance

### Backup Strategy
- Supabase automatically handles backups for Pro plans
- For additional safety, consider regular manual exports

### Monitoring
- Use Supabase dashboard to monitor:
  - Database performance
  - Query execution times
  - Storage usage
  - API usage

### Schema Updates
- Always test schema changes in a development environment first
- Use migrations for production schema updates
- Keep this README updated with any schema changes

## 🔗 Next Steps

After setting up the database:

1. Configure your backend to connect to Supabase
2. Set up authentication in your frontend
3. Test the API endpoints with the new schema
4. Implement campaign creation and management features

For detailed API documentation, see the main project README.
