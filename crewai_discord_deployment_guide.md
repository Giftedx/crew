# Enhanced CrewAI Discord Intelligence System - Complete Deployment Guide

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Installation Setup](#pre-installation-setup)
3. [Installation Process](#installation-process)
4. [Configuration](#configuration)
5. [API Keys Setup](#api-keys-setup)
6. [Database Setup](#database-setup)
7. [Discord Setup](#discord-setup)
8. [First Run](#first-run)
9. [Production Deployment](#production-deployment)
10. [Monitoring & Maintenance](#monitoring--maintenance)
11. [Troubleshooting](#troubleshooting)

## 🖥️ System Requirements

### Hardware Requirements

**Minimum:**
- CPU: 4-core processor (Intel i5 or AMD Ryzen 5 equivalent)
- RAM: 16GB (32GB recommended for large-scale processing)
- Storage: 1TB+ available space on F:/ drive (or equivalent)
- Network: High-speed internet connection (100Mbps+ recommended)

**Recommended (Production):**
- CPU: 8-core processor with high single-thread performance
- RAM: 32GB+ with fast memory speeds
- Storage: 2TB+ NVMe SSD for processing, additional HDD for long-term storage
- Network: Gigabit connection with low latency

### Software Requirements

**Operating System:**
- Windows 10/11 (Primary support)
- Linux (Ubuntu 20.04+ or equivalent)
- macOS (Limited support)

**Required Software:**
- Python 3.10-3.13 (not 3.14+)
- FFmpeg (latest version)
- Git
- Chrome/Chromium browser
- Node.js (for optional web interface)

## 🛠️ Pre-Installation Setup

### 1. Create Directory Structure

```powershell
# Create base directories on F:/ drive (Windows)
New-Item -ItemType Directory -Path "F:\yt-auto\crewaiv2\CrewAI_Content_System" -Force
New-Item -ItemType Directory -Path "F:\yt-auto\crewaiv2\yt-dlp\config" -Force

# On Linux/macOS, adjust paths accordingly
mkdir -p /opt/crewai-system/{downloads,config,logs}
```

### 2. Install System Dependencies

**Windows:**
```powershell
# Install Chocolatey (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install dependencies
choco install python310 ffmpeg git googlechrome nodejs -y
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip ffmpeg git chromium-browser nodejs npm
```

**macOS:**
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.10 ffmpeg git chromium node
```

### 3. Install yt-dlp

```bash
# Install yt-dlp globally
pip install --upgrade yt-dlp

# Or download standalone executable (Windows)
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe -o F:\yt-dlp\yt-dlp.exe
```

## 📦 Installation Process

### 1. Clone Repository

```bash
git clone https://github.com/your-repo/enhanced-crewai-system.git
cd enhanced-crewai-system
```

### 2. Create Python Virtual Environment

```bash
# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
# Install core requirements
pip install --upgrade pip
pip install -r requirements.txt

# Install optional dependencies for enhanced features
pip install -r requirements-optional.txt
```

### 4. Install Additional AI Models

```bash
# Install Whisper models (for transcription)
python -c "import whisper; whisper.load_model('base')"

# Install NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon'); nltk.download('stopwords')"
```

## ⚙️ Configuration

### 1. Create Configuration Files

```bash
# Copy configuration templates
cp config/system_config.yaml.template config/system_config.yaml
cp config/channels.yaml.template config/channels.yaml
cp config/discord_channels.yaml.template config/discord_channels.yaml
cp .env.template .env
```

### 2. Configure System Paths

Edit `config/system_config.yaml`:

```yaml
paths:
  base_dir: "F:/yt-auto/crewaiv2/CrewAI_Content_System"  # Adjust for your system
  downloads_dir: "F:/yt-auto/crewaiv2/CrewAI_Content_System/Downloads"
  config_dir: "F:/yt-auto/crewaiv2/CrewAI_Content_System/Config"
  logs_dir: "F:/yt-auto/crewaiv2/CrewAI_Content_System/Logs"
  processing_dir: "F:/yt-auto/crewaiv2/CrewAI_Content_System/Processing"
  ytdlp_config: "F:/yt-auto/crewaiv2/yt-dlp/config/crewai-system.conf"
  google_credentials: "F:/yt-auto/crewaiv2/CrewAI_Content_System/Config/google-credentials.json"
```

### 3. Configure Content Sources

Edit `config/channels.yaml`:

```yaml
youtube_channels:
  - "https://www.youtube.com/channel/UC_CHANNEL_ID_1"
  - "https://www.youtube.com/channel/UC_CHANNEL_ID_2"

instagram_accounts:
  - "username1"
  - "username2"

monitoring:
  interval: 300  # 5 minutes
  enable_pubsubhubbub: true
  webhook_url: "https://your-domain.com/youtube-webhook"
```

### 4. Configure Discord Integration

Edit `config/discord_channels.yaml`:

```yaml
channels:
  - name: "youtube-content"
    id: "YOUR_DISCORD_CHANNEL_ID"
    webhook_url: "YOUR_DISCORD_WEBHOOK_URL"
    max_file_size: 100000000  # 100MB
    allowed_types: ["video/*", "image/*"]
  
  - name: "instagram-content"
    id: "YOUR_DISCORD_CHANNEL_ID_2"
    webhook_url: "YOUR_DISCORD_WEBHOOK_URL_2"
    max_file_size: 50000000   # 50MB

  - name: "system-alerts"
    id: "YOUR_ALERTS_CHANNEL_ID"
    webhook_url: "YOUR_ALERTS_WEBHOOK_URL"
```

## 🔑 API Keys Setup

### 1. Required API Keys

Edit `.env` file with your API keys:

```bash
# Essential (System won't work without these)
OPENAI_API_KEY=your_openai_api_key_here
SERPLY_API_KEY=your_serply_api_key_here  # For fact-checking
EXA_API_KEY=your_exa_api_key_here        # For advanced search

# Discord Integration
DISCORD_WEBHOOK_URL=your_primary_webhook_url

# Google Services (for Drive/Sheets integration)
# Place google-credentials.json in Config/ directory

# Optional but Recommended
SCRAPEGRAPH_API_KEY=your_scrapegraph_key  # Enhanced web scraping
BROWSERBASE_API_KEY=your_browserbase_key  # Web automation
BROWSERBASE_PROJECT_ID=your_project_id

# Social Media APIs (Optional)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
ROCKET_API_KEY=your_rocket_api_key       # Instagram API
HUGGINGFACE_TOKEN=your_hf_token          # AI models

# Instagram Login (if using Instaloader)
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
```

### 2. Obtaining API Keys

**OpenAI API:**
1. Visit https://platform.openai.com/api-keys
2. Create new API key
3. Set usage limits to prevent overspending

**Serply API:**
1. Visit https://serply.io/
2. Sign up for account
3. Choose appropriate plan for your needs

**EXA API:**
1. Visit https://exa.ai/
2. Sign up and get API key
3. Start with free tier

**Google Services:**
1. Go to Google Cloud Console
2. Create new project or select existing
3. Enable Google Drive API and Google Sheets API
4. Create service account
5. Download JSON credentials file
6. Place in Config directory as `google-credentials.json`

### 3. API Key Security

```bash
# Set proper permissions on .env file (Linux/macOS)
chmod 600 .env

# On Windows, restrict file access through Properties > Security
```

## 🗄️ Database Setup

### 1. Vector Database (Qdrant)

**Option A: Cloud Qdrant**
1. Visit https://cloud.qdrant.io/
2. Create cluster
3. Get connection URL and API key
4. Add to configuration:

```yaml
storage:
  qdrant_url: "https://your-cluster.qdrant.io:6333"
  qdrant_api_key: "your_api_key"
```

**Option B: Local Qdrant**
```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Add to configuration
storage:
  qdrant_url: "http://localhost:6333"
  qdrant_api_key: ""  # Leave empty for local
```

### 2. File Storage Structure

The system will automatically create:
```
F:/yt-auto/crewaiv2/CrewAI_Content_System/
├── Downloads/
│   ├── YouTube/
│   │   └── [Creator_Name]/[Year]/[Month]/
│   └── Instagram/
│       ├── Stories/[Username]/
│       ├── Posts/[Username]/
│       └── Lives/[Username]/
├── Analysis/
│   ├── Transcripts/
│   ├── Speaker_Profiles/
│   └── Fact_Checks/
├── GoogleDrive/
│   ├── Uploaded/
│   └── Pending/
└── Logs/
    ├── system.log
    ├── downloads.log
    └── discord.log
```

## 💬 Discord Setup

### 1. Create Discord Server

1. Create new Discord server or use existing
2. Create channels for different content types:
   - `#youtube-content`
   - `#instagram-content`
   - `#system-alerts`
   - `#fact-checks`
   - `#qa-system`

### 2. Create Webhooks

For each channel:
1. Go to Channel Settings > Integrations
2. Create New Webhook
3. Customize name and avatar
4. Copy webhook URL
5. Add to `discord_channels.yaml`

### 3. Set Permissions

Ensure the webhook has permissions to:
- Send Messages
- Embed Links
- Attach Files
- Manage Threads (for Q&A system)

## 🚀 First Run

### 1. Configuration Validation

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run configuration check
python -m enhanced_system_config --check-health
```

### 2. Test Individual Components

```bash
# Test YouTube monitoring
python -c "from enhanced_youtube_monitor import EnhancedYouTubeDownloadTool; tool = EnhancedYouTubeDownloadTool(); print('YouTube tool ready')"

# Test Instagram monitoring
python -c "from enhanced_instagram_manager import EnhancedInstagramContentTool; tool = EnhancedInstagramContentTool(); print('Instagram tool ready')"

# Test Discord integration
python -c "from enhanced_discord_manager import EnhancedDiscordBotTool; print('Discord integration ready')"
```

### 3. Run System Health Check

```bash
python enhanced_crewai_system.py --health-check
```

Expected output:
```
🏥 System Health Check
Overall Status: HEALTHY
Timestamp: 2024-01-15T10:30:00Z

Configuration:
  overall_status: healthy
  apis: openai_api_key: configured, serply_api_key: configured
  directories: all directories exist
  google_credentials: found

Resources:
  disk_space_gb: 500.2
  memory_percent: 45.2
  cpu_percent: 12.1
  status: good
```

### 4. First System Run

```bash
# Start the system
python enhanced_crewai_system.py --run
```

Monitor the output for:
- ✅ Configuration loading
- ✅ Agent initialization
- ✅ Task execution
- ✅ Content processing
- ✅ Discord posting

## 🏭 Production Deployment

### 1. Process Management

**Option A: systemd (Linux)**

Create `/etc/systemd/system/crewai-system.service`:

```ini
[Unit]
Description=Enhanced CrewAI Discord Intelligence System
After=network.target

[Service]
Type=simple
User=crewai
Group=crewai
WorkingDirectory=/opt/crewai-system
Environment=PATH=/opt/crewai-system/venv/bin
ExecStart=/opt/crewai-system/venv/bin/python enhanced_crewai_system.py --run
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable crewai-system
sudo systemctl start crewai-system
```

**Option B: Docker Deployment**

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  crewai-system:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SERPLY_API_KEY=${SERPLY_API_KEY}
      - EXA_API_KEY=${EXA_API_KEY}
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    restart: unless-stopped
    ports:
      - "8080:8080"  # Health check endpoint

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  qdrant_data:
  grafana_data:
```

### 2. Monitoring Setup

**Prometheus Configuration** (`monitoring/prometheus.yml`):

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'crewai-system'
    static_configs:
      - targets: ['crewai-system:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

**Health Check Endpoint**

The system exposes health metrics at `http://localhost:8080/health`:

```json
{
  "status": "healthy",
  "uptime": 3600,
  "metrics": {
    "videos_processed": 42,
    "success_rate": 0.95
  },
  "components": {
    "youtube_monitor": "healthy",
    "discord_integration": "healthy"
  }
}
```

### 3. Backup Strategy

```bash
#!/bin/bash
# backup.sh - Daily backup script

BACKUP_DIR="/backup/crewai-$(date +%Y%m%d)"
SOURCE_DIR="/opt/crewai-system"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp -r "$SOURCE_DIR/config" "$BACKUP_DIR/"

# Backup analysis results
tar -czf "$BACKUP_DIR/analysis_data.tar.gz" "$SOURCE_DIR/Analysis"

# Backup vector database
docker exec qdrant qdrant-backup > "$BACKUP_DIR/qdrant_backup.sql"

# Upload to cloud storage (optional)
# aws s3 sync "$BACKUP_DIR" "s3://your-backup-bucket/$(basename $BACKUP_DIR)"

# Cleanup old backups (keep 30 days)
find /backup -name "crewai-*" -mtime +30 -exec rm -rf {} \;
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /opt/crewai-system/backup.sh
```

## 📊 Monitoring & Maintenance

### 1. Log Management

**Log Rotation** (`/etc/logrotate.d/crewai-system`):

```
/opt/crewai-system/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 crewai crewai
    postrotate
        systemctl reload crewai-system
    endscript
}
```

### 2. Performance Monitoring

**Key Metrics to Monitor:**
- Processing time per video
- Success/failure rates
- Memory usage
- Disk space usage
- API rate limit usage
- Discord posting success rates

**Grafana Dashboard Queries:**
```promql
# Processing success rate
rate(crewai_videos_processed_total[5m]) / rate(crewai_operations_total[5m])

# Average processing time
rate(crewai_processing_time_seconds_total[5m]) / rate(crewai_videos_processed_total[5m])

# Error rate
rate(crewai_errors_total[5m])
```

### 3. Maintenance Tasks

**Weekly Tasks:**
```bash
#!/bin/bash
# weekly_maintenance.sh

# Update system packages
apt update && apt upgrade -y

# Update Python packages
source /opt/crewai-system/venv/bin/activate
pip install --upgrade -r requirements.txt

# Clean temporary files
find /opt/crewai-system/data/temp -mtime +7 -delete

# Restart services
systemctl restart crewai-system
```

**Monthly Tasks:**
- Review and rotate API keys
- Clean up old analysis data
- Update AI models (Whisper, etc.)
- Review and optimize configuration
- Performance analysis and tuning

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. "Failed to initialize transcription models"

**Cause:** Missing dependencies or insufficient system resources

**Solution:**
```bash
# Install missing dependencies
pip install torch torchvision torchaudio
pip install openai-whisper

# For systems without CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Check system resources
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

#### 2. "Rate limited by Discord"

**Cause:** Exceeding Discord webhook rate limits

**Solution:**
- Reduce posting frequency in configuration
- Implement additional delay between posts
- Use multiple webhooks for different content types

#### 3. "Google Drive upload failed"

**Cause:** Invalid credentials or API limits

**Solution:**
```bash
# Verify credentials
python -c "
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_file('config/google-credentials.json')
print('Credentials valid')
"

# Check API quotas in Google Cloud Console
```

#### 4. "YouTube download failed"

**Cause:** yt-dlp outdated or blocked

**Solution:**
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Use different user agent
echo '--user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"' >> F:/yt-dlp/config/crewai-system.conf
```

#### 5. "High memory usage"

**Cause:** Large files or memory leaks

**Solutions:**
- Reduce concurrent processing
- Implement memory cleanup
- Use smaller AI models
- Add swap space

```bash
# Add swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Debug Mode

Enable debug mode for detailed logging:

```yaml
# In system_config.yaml
system:
  debug: true
  log_level: DEBUG

# Or via environment variable
export CREWAI_DEBUG=true
```

### Log Analysis

```bash
# Check for errors
grep -i error /opt/crewai-system/logs/system.log | tail -20

# Monitor real-time logs
tail -f /opt/crewai-system/logs/system.log

# Check component-specific logs
tail -f /opt/crewai-system/logs/downloads.log
tail -f /opt/crewai-system/logs/discord.log
```

### Performance Profiling

```python
# Add to debug runs
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run system
crew_system.run_with_monitoring(inputs)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

## 📞 Support and Community

- **Documentation:** Check the latest documentation updates
- **Issues:** Report bugs and issues on GitHub
- **Community:** Join the Discord community for support
- **Updates:** Subscribe to release notifications

---

## 🎯 Quick Start Checklist

- [ ] System requirements met
- [ ] Dependencies installed
- [ ] Configuration files created
- [ ] API keys obtained and configured
- [ ] Discord server and webhooks set up
- [ ] Google Drive credentials configured
- [ ] Health check passed
- [ ] First successful run completed
- [ ] Monitoring set up
- [ ] Backup strategy implemented

**Estimated Setup Time:** 2-4 hours for basic setup, additional time for production hardening.

For additional support, consult the troubleshooting section or reach out to the community.