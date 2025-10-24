# Phase 1 Environment Setup Guide

## Current Status Assessment

Based on the Phase 1 environment setup report, here's what needs to be configured:

### ❌ Critical Issues (Must Fix)

1. **Missing Required Environment Variables**
   - `DISCORD_BOT_TOKEN` - Required for Discord bot functionality
   - `OPENAI_API_KEY` - Required for LLM functionality
   - `QDRANT_URL` - Required for vector database

2. **Service Dependencies Not Running**
   - Qdrant vector database (port 6333)
   - MinIO object storage (port 9000)
   - PostgreSQL database (port 5432)
   - Redis cache (port 6379)

3. **OAuth Configuration Missing**
   - All platform OAuth credentials (YouTube, Twitch, TikTok, Instagram, X)

### ⚠️ Optional Issues (Should Fix)

1. **Optional Environment Variables**
   - `OPENROUTER_API_KEY` - Alternative LLM provider
   - `POSTGRES_URL` - Database connection
   - `REDIS_URL` - Cache connection
   - `MINIO_URL` - Object storage connection

## Phase 1 Minimal Configuration

For Phase 1 implementation, we need to set up the minimal required configuration to get the system operational.

### Step 1: Environment Variables Setup

Create a `.env` file with the following minimal configuration:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your actual values
nano .env
```

**Required Variables:**

```bash
# Discord Bot Token (get from Discord Developer Portal)
DISCORD_BOT_TOKEN=your-actual-discord-bot-token

# OpenAI API Key (get from OpenAI Platform)
OPENAI_API_KEY=sk-your-actual-openai-key

# Qdrant Vector Database URL
QDRANT_URL=http://localhost:6333

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Optional Variables (for full functionality):**

```bash
# OpenRouter API Key (alternative LLM provider)
OPENROUTER_API_KEY=sk-your-openrouter-key

# Database URLs
POSTGRES_URL=postgresql://localhost:5432/ultimate_discord_intelligence_bot
REDIS_URL=redis://localhost:6379/0
MINIO_URL=http://localhost:9000

# OAuth Credentials (for content platform access)
YOUTUBE_CLIENT_ID=your-youtube-client-id
YOUTUBE_CLIENT_SECRET=your-youtube-client-secret
TWITCH_CLIENT_ID=your-twitch-client-id
TWITCH_CLIENT_SECRET=your-twitch-client-secret
TIKTOK_CLIENT_ID=your-tiktok-client-id
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret
INSTAGRAM_CLIENT_ID=your-instagram-client-id
INSTAGRAM_CLIENT_SECRET=your-instagram-client-secret
X_CLIENT_ID=your-x-client-id
X_CLIENT_SECRET=your-x-client-secret
```

### Step 2: Service Dependencies Setup

Since Docker is not available in this WSL environment, we have several options:

#### Option A: Use Cloud Services (Recommended for Phase 1)

- **Qdrant Cloud**: Use Qdrant's cloud service instead of local instance
- **PostgreSQL Cloud**: Use a cloud PostgreSQL service (AWS RDS, Google Cloud SQL, etc.)
- **Redis Cloud**: Use a cloud Redis service (AWS ElastiCache, Redis Cloud, etc.)

#### Option B: Install Services Locally

```bash
# Install Qdrant locally
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz | tar xz
./qdrant

# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server

# Install MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server /tmp/minio
```

#### Option C: Use Docker Desktop (if available)

```bash
# Start services with Docker Compose
docker-compose up -d qdrant postgres redis minio
```

### Step 3: OAuth Setup (Optional for Phase 1)

OAuth credentials are required for accessing content from external platforms. For Phase 1, we can proceed without them and add them later.

**To get OAuth credentials:**

1. Go to each platform's developer portal
2. Create a new application
3. Get the Client ID and Client Secret
4. Add them to your `.env` file

**Platforms:**

- YouTube: <https://console.developers.google.com/>
- Twitch: <https://dev.twitch.tv/console/apps>
- TikTok: <https://developers.tiktok.com/>
- Instagram: <https://developers.facebook.com/>
- X (Twitter): <https://developer.twitter.com/>

## Phase 1 Implementation Strategy

### Immediate Actions (Today)

1. **Set up minimal environment variables**
   - Discord Bot Token
   - OpenAI API Key
   - Qdrant URL (use cloud service)

2. **Configure cloud services**
   - Set up Qdrant Cloud account
   - Configure Qdrant URL in environment

3. **Test basic functionality**
   - Run doctor check
   - Test basic bot functionality

### Short-term Actions (This Week)

1. **Complete service setup**
   - Set up remaining cloud services
   - Configure all environment variables

2. **OAuth configuration**
   - Set up OAuth credentials for at least one platform
   - Test OAuth flows

3. **End-to-end testing**
   - Test complete workflows
   - Validate all integrations

## Testing the Setup

After configuration, test the setup:

```bash
# Test environment configuration
python3 scripts/setup_phase1_environment.py --check-only

# Test system health
make doctor

# Test basic functionality
python3 -m ultimate_discord_intelligence_bot.main --help
```

## Troubleshooting

### Common Issues

1. **"Connection refused" errors**
   - Services are not running
   - Check service status and start them

2. **"Module not found" errors**
   - Python path issues
   - Install dependencies: `pip install -r requirements.txt`

3. **"API key invalid" errors**
   - Check API key format and validity
   - Ensure keys are properly set in environment

4. **"OAuth authentication failed"**
   - Check OAuth credentials
   - Verify redirect URIs in platform settings

## Next Steps

Once the minimal configuration is working:

1. **Phase 1.2**: Set up SLO monitoring
2. **Phase 1.3**: Complete service integration
3. **Phase 1.4**: Production deployment
4. **Phase 1.5**: Performance optimization

---

**Status**: Ready for implementation
**Priority**: Critical
**Estimated Time**: 2-4 hours for minimal setup
