# Installation Guide

## Quick Start (Minimal Installation)

For basic functionality with core features:

```bash
pip install ultimate-discord-intelligence-bot
```

This installs only the essential dependencies for:

- Discord bot functionality
- Basic content analysis
- Vector storage with Qdrant
- Core AI/ML capabilities

## Full Installation

For complete functionality with all features:

```bash
pip install ultimate-discord-intelligence-bot[all]
```

This includes:

- All core features
- Machine learning capabilities
- Computer vision processing
- Advanced memory systems
- Development tools
- Documentation tools

## Specialized Installations

### Machine Learning Features

```bash
pip install ultimate-discord-intelligence-bot[ml]
```

Includes: PyTorch, Transformers, Scikit-learn, NumPy, Pandas

### Computer Vision Features

```bash
pip install ultimate-discord-intelligence-bot[vision]
```

Includes: OpenCV, Pillow, ImageIO, Scikit-image

### Advanced Memory Systems

```bash
pip install ultimate-discord-intelligence-bot[memory]
```

Includes: ChromaDB, Mem0, NetworkX, Neo4j

### Development Tools

```bash
pip install ultimate-discord-intelligence-bot[dev]
```

Includes: Pytest, Black, Ruff, MyPy, Pre-commit

### Documentation Tools

```bash
pip install ultimate-discord-intelligence-bot[docs]
```

Includes: MkDocs, MkDocs-Material, Mkdocstrings

## Environment Setup

1. **Create virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   # Minimal installation
   pip install ultimate-discord-intelligence-bot
   
   # Or full installation
   pip install ultimate-discord-intelligence-bot[all]
   ```

3. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Docker Installation

For containerized deployment:

```bash
# Build with minimal dependencies
docker build -t ultimate-discord-bot:minimal .

# Build with full dependencies
docker build -t ultimate-discord-bot:full --target full .
```

## System Requirements

### Minimal Installation

- Python 3.10+
- 2GB RAM
- 1GB disk space

### Full Installation

- Python 3.10+
- 8GB RAM (for ML models)
- 5GB disk space
- CUDA support (optional, for GPU acceleration)

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you have the correct optional dependencies installed
2. **Memory issues**: Use minimal installation for resource-constrained environments
3. **CUDA errors**: Install CPU-only versions of PyTorch if GPU is not available

### Getting Help

- Check the [Configuration Guide](configuration.md)
- Review [Troubleshooting Guide](troubleshooting.md)
- Join our Discord server for support
