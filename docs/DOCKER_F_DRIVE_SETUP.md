# Installing Docker on F Drive with Large AI Models

## Overview

This guide shows you how to install Docker Desktop on your F drive (instead of the default C drive) and configure it for large AI model storage. This is particularly useful when working with large language models that can be 60-100GB+ in size.

## Why Install on F Drive?

- **Space**: C drive often has limited space; F drive typically has more storage
- **Performance**: Dedicated drive for Docker can improve I/O performance
- **Organization**: Keep system files separate from Docker data/models
- **Large Models**: AI models like `gpt-oss:120B-UD-Q4_K_XL` require significant storage

## Prerequisites

1. **Windows 10/11** with administrator access
1. **F drive** with at least 200GB free space (recommended for large models)
1. **WSL2** installed (required for Docker Desktop)

## Step 1: Install Docker Desktop

### Download and Initial Setup

1. Download Docker Desktop from: <https://docs.docker.com/desktop/install/windows-install/>
1. Run the installer
1. When prompted, select:
   - ✅ Use WSL 2 instead of Hyper-V
   - ✅ Add shortcut to desktop

**Important**: Complete the installation but **do not start Docker Desktop yet**.

## Step 2: Move Docker Data to F Drive

### Option A: Clean Installation (Recommended)

If you haven't started Docker Desktop yet:

1. **Create Docker directory on F drive**:

   ```powershell
   # Run in PowerShell as Administrator
   New-Item -Path "F:\Docker" -ItemType Directory
   New-Item -Path "F:\Docker\wsl" -ItemType Directory
   ```

1. **Create Docker Desktop settings file**:

   ```powershell
   # Create settings directory
   $dockerConfigPath = "$env:APPDATA\Docker"
   New-Item -Path $dockerConfigPath -ItemType Directory -Force

   # Create settings.json with F drive path
   @"
   {
     "dataFolder": "F:\\Docker\\data",
     "wslEngineEnabled": true
   }
   "@ | Out-File -FilePath "$dockerConfigPath\settings.json" -Encoding utf8
   ```

1. **Start Docker Desktop** and verify the data location in Settings → Resources → Advanced

### Option B: Move Existing Installation

If Docker is already installed on C drive:

1. **Stop Docker Desktop** completely (right-click system tray → Quit Docker Desktop)

1. **Stop WSL**:

   ```powershell
   wsl --shutdown
   ```

1. **Export WSL distros**:

   ```powershell
   # Export docker-desktop
   wsl --export docker-desktop F:\Docker\wsl\docker-desktop.tar

   # Export docker-desktop-data
   wsl --export docker-desktop-data F:\Docker\wsl\docker-desktop-data.tar
   ```

1. **Unregister old distros**:

   ```powershell
   wsl --unregister docker-desktop
   wsl --unregister docker-desktop-data
   ```

1. **Import to F drive**:

   ```powershell
   # Import docker-desktop
   wsl --import docker-desktop F:\Docker\wsl\distro\docker-desktop F:\Docker\wsl\docker-desktop.tar --version 2

   # Import docker-desktop-data
   wsl --import docker-desktop-data F:\Docker\wsl\distro\docker-desktop-data F:\Docker\wsl\docker-desktop-data.tar --version 2
   ```

1. **Update Docker Desktop settings**:

   Edit `%APPDATA%\Docker\settings.json`:

   ```json
   {
     "dataFolder": "F:\\Docker\\data",
     "wslEngineEnabled": true
   }
   ```

1. **Clean up** (after verifying everything works):

   ```powershell
   Remove-Item F:\Docker\wsl\docker-desktop.tar
   Remove-Item F:\Docker\wsl\docker-desktop-data.tar
   ```

## Step 3: Configure Docker Desktop

1. **Start Docker Desktop**

1. **Open Settings** (gear icon or system tray → Settings)

1. **Resources → Advanced**:
   - Memory: 8GB+ (for large models)
   - CPUs: 4+ cores
   - Disk image size: 200GB+ (adjust based on F drive space)

1. **Resources → WSL Integration**:
   - ✅ Enable integration with my default WSL distro
   - ✅ Enable integration with additional distros (select your Ubuntu/distro)
   - Click **Apply & Restart**

1. **Resources → Disk Image Location** (verify):
   - Should show `F:\Docker\data` or similar F drive path

## Step 4: Verify Installation

### From PowerShell (Windows)

```powershell
# Check Docker version
docker --version

# Check Docker is using F drive
docker info | Select-String "Docker Root Dir"

# Test with hello-world
docker run hello-world
```

### From WSL2 (Ubuntu/Your Distro)

```bash
# Check Docker is accessible
docker --version
docker compose version

# Verify storage location
docker info | grep "Docker Root Dir"
```

## Step 5: Pull Large AI Models

### Understanding the Model Command

The command `docker model pull ai/gpt-oss:120B-UD-Q4_K_XL` suggests you're working with AI models. Depending on your setup:

### Option A: Standard Docker Registry

If the model is hosted on a Docker registry:

```bash
# Standard Docker pull
docker pull ai/gpt-oss:120B-UD-Q4_K_XL

# Verify image
docker images | grep gpt-oss
```

### Option B: Ollama Models

If you're using Ollama (common for running local LLMs):

1. **Install Ollama**:

   ```powershell
   # Download from https://ollama.ai/download
   # Or via Docker:
   docker pull ollama/ollama
   ```

1. **Run Ollama container** (uses F drive storage):

   ```bash
   docker run -d \
     --name ollama \
     -v F:/Docker/ollama:/root/.ollama \
     -p 11434:11434 \
     ollama/ollama
   ```

1. **Pull the model**:

   ```bash
   # If using Ollama container
   docker exec -it ollama ollama pull llama2:70b

   # Or if Ollama is installed on Windows:
   ollama pull llama2:70b
   ```

### Option C: Hugging Face / Custom Registry

If the model is from a custom registry:

```bash
# Pull from specific registry
docker pull registry.example.com/ai/gpt-oss:120B-UD-Q4_K_XL

# Or with authentication
docker login registry.example.com
docker pull registry.example.com/ai/gpt-oss:120B-UD-Q4_XL
```

## Storage Management

### Check Disk Usage

```bash
# Docker disk usage
docker system df

# Detailed view
docker system df -v

# WSL disk usage (from PowerShell)
wsl --list --verbose
```

### Clean Up Space

```bash
# Remove unused images
docker image prune -a

# Remove unused containers
docker container prune

# Remove everything unused
docker system prune -a --volumes

# Compact WSL disk (from PowerShell)
wsl --shutdown
Optimize-VHD -Path "F:\Docker\wsl\distro\docker-desktop-data\ext4.vhdx" -Mode Full
```

## Disk Space Requirements

| Model Size | Quantization | Approximate Storage | RAM Required |
|------------|--------------|---------------------|--------------|
| 7B params  | Q4_K_M      | ~4GB               | 8GB          |
| 13B params | Q4_K_M      | ~8GB               | 12GB         |
| 70B params | Q4_K_M      | ~40GB              | 48GB         |
| 120B params| Q4_K_XL     | ~70-80GB           | 80GB+        |

**For `gpt-oss:120B-UD-Q4_K_XL`**: Expect ~70-100GB storage + 80GB+ RAM

## Troubleshooting

### "Not enough space" Error

1. **Check F drive space**:

   ```powershell
   Get-PSDrive F
   ```

1. **Increase Docker disk size**:
   - Settings → Resources → Advanced → Disk image size
   - Increase to 250GB or more

1. **Compact existing images**:

   ```bash
   docker system prune -a
   ```

### WSL Distro Not Found

```powershell
# List all WSL distros
wsl --list --verbose

# If docker-desktop distros are missing, reimport:
wsl --import docker-desktop F:\Docker\wsl\distro\docker-desktop F:\Docker\wsl\docker-desktop.tar --version 2
```

### Docker Desktop Won't Start

1. **Check logs**: `%APPDATA%\Docker\log.txt`
1. **Reset to factory defaults**: Settings → Troubleshoot → Reset to factory defaults
1. **Reinstall**: Uninstall Docker Desktop, delete `F:\Docker`, reinstall

### Model Pull Fails

```bash
# Check registry connectivity
docker pull hello-world

# Check authentication
docker login

# Verify image name/tag
# Common issues:
# - Typo in image name
# - Wrong registry URL
# - Missing credentials
# - Network/firewall blocking registry
```

## Running Your Project on F Drive

Once Docker is configured on F drive, your project will automatically use it:

```bash
# Navigate to project (in WSL)
cd /home/crew

# Build (uses F drive storage)
docker compose -f config/docker/docker-compose.yml build

# Run (containers and volumes on F drive)
docker compose -f config/docker/docker-compose.yml up -d

# Verify
docker ps
docker volume ls
```

## Moving WSL Project to F Drive (Optional)

If you want your WSL filesystem on F drive too:

### Export Current Distro

```powershell
# From Windows PowerShell
wsl --shutdown

# Export your Ubuntu/distro
wsl --export Ubuntu F:\WSL\ubuntu-backup.tar

# Unregister old location
wsl --unregister Ubuntu

# Import to F drive
wsl --import Ubuntu F:\WSL\Ubuntu F:\WSL\ubuntu-backup.tar --version 2

# Set as default
wsl --set-default Ubuntu
```

### Access Project

```bash
# Your project files are now at:
# F:\WSL\Ubuntu\home\crew

# Or from WSL:
cd /home/crew
```

## Performance Tips

1. **Disable Windows Defender real-time scanning** for Docker directories:
   - Settings → Windows Security → Virus & threat protection → Manage settings
   - Add exclusions: `F:\Docker\` and `F:\WSL\`

1. **Use SSD for F drive** if possible (much faster than HDD)

1. **Allocate sufficient resources**:
   - Memory: At least half your system RAM
   - CPUs: At least half your cores
   - For 120B model: 80GB+ RAM recommended

1. **Enable BuildKit** for faster builds:

   ```powershell
   $env:DOCKER_BUILDKIT=1
   ```

## Model-Specific Commands

### Running the GPT Model

Once pulled, run the model:

```bash
# If it's a Docker image
docker run -it --rm \
  --gpus all \
  -v F:/Docker/models:/models \
  ai/gpt-oss:120B-UD-Q4_K_XL

# If using Ollama
ollama run gpt-oss:120b-ud-q4_k_xl
```

### Serving the Model

```bash
# Example API server for the model
docker run -d \
  --name gpt-server \
  --gpus all \
  -p 8080:8080 \
  -v F:/Docker/models:/models \
  ai/gpt-oss:120B-UD-Q4_K_XL \
  serve --port 8080
```

## Verification Checklist

- ✅ Docker Desktop installed
- ✅ Data directory on F drive (`F:\Docker\data` or similar)
- ✅ WSL2 integration enabled
- ✅ `docker --version` works from WSL
- ✅ `docker info` shows F drive path
- ✅ At least 200GB free on F drive
- ✅ Model pulled successfully
- ✅ Project containers build and run

## Quick Reference

```bash
# Check Docker location
docker info | grep "Docker Root Dir"

# Check disk usage
docker system df

# Pull model (adjust command based on your registry)
docker pull ai/gpt-oss:120B-UD-Q4_K_XL

# List models/images
docker images

# Run model (example)
docker run -it --rm ai/gpt-oss:120B-UD-Q4_K_XL

# Clean up
docker system prune -a
```

## Related Documentation

- [Docker Desktop WSL2 Setup](./DOCKER_WSL2_SETUP.md) - General WSL2 integration
- [Project README](../README.md) - Main project documentation
- [Setup Complete](../SETUP_COMPLETE_2025-11-04.md) - Current setup status

## Support

- **Docker Desktop**: <https://docs.docker.com/desktop/troubleshoot/overview/>
- **WSL2**: <https://docs.microsoft.com/windows/wsl/troubleshooting>
- **Ollama**: <https://ollama.ai/docs>
- **Model Registry**: Check with your model provider for specific instructions

---

**Note**: The exact command for pulling your model depends on which registry/system you're using. If `docker model pull` isn't recognized, it's likely an Ollama command or custom tooling. Please verify the model source and adjust commands accordingly.
