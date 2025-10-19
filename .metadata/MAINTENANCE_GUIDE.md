# 🔧 Repository Maintenance Guide
**Ultimate Discord Intelligence Bot**  
**Created:** October 17, 2025

---

## 🚀 Quick Start

### Automated Maintenance Scripts

All maintenance scripts are located in:
```
scripts/utilities/maintenance/
├── cleanup_repository.sh    # General cleanup
├── archive_old_files.sh    # Archive old files  
└── optimize_venv.sh        # Optimize virtual environment
```

---

## 📋 Regular Maintenance Tasks

### Daily (Automated via Pre-commit Hooks)
- Python cache cleanup (`__pycache__`, `.pyc`)
- Temporary file removal (`.tmp`, `.swp`, `~`)

### Weekly Cleanup
```bash
# Basic cleanup (recommended)
./scripts/utilities/maintenance/cleanup_repository.sh

# Aggressive cleanup (removes empty dirs)
./scripts/utilities/maintenance/cleanup_repository.sh --remove-empty
```

### Monthly Archive
```bash
# Archive files older than 30 days (default)
./scripts/utilities/maintenance/archive_old_files.sh

# Archive files older than 60 days
./scripts/utilities/maintenance/archive_old_files.sh 60

# Archive files older than 90 days
./scripts/utilities/maintenance/archive_old_files.sh 90
```

### Quarterly Optimization
```bash
# Optimize virtual environment
./scripts/utilities/maintenance/optimize_venv.sh

# Aggressive optimization with compaction
./scripts/utilities/maintenance/optimize_venv.sh --compact
```

---

## 📂 Directory-Specific Maintenance

### crew_data/Downloads/ (93M)
**Issue:** Accumulates downloaded content  
**Solution:**
```bash
# Review and clean monthly
ls -lah crew_data/Downloads/
# Archive old downloads
./scripts/utilities/maintenance/archive_old_files.sh 30
```

### benchmarks/results/ (9.9M)
**Issue:** Accumulates test results  
**Solution:**
```bash
# Quarterly archive
find benchmarks/results -name "*.json" -mtime +90 \
  -exec mv {} archive/benchmarks/ \;
```

### archive/ (93M)
**Issue:** Grows over time  
**Solution:**
```bash
# Annual review
du -sh archive/*
# Consider external backup for files > 1 year old
```

### cache/ (148K)
**Issue:** Cache invalidation  
**Solution:**
```bash
# Clear if experiencing issues
rm -rf cache/semantic/*
# Cache will rebuild automatically
```

---

## 🛠️ Manual Maintenance Tasks

### 1. Check for Large Files
```bash
# Find files larger than 10MB
find . -type f -size +10M -not -path "./venv/*" \
  -not -path "./.git/*" -exec ls -lh {} \;
```

### 2. Find Duplicate Files
```bash
# Find potential duplicates by name
find . -type f -not -path "./venv/*" \
  -exec basename {} \; | sort | uniq -d
```

### 3. Clean Docker Artifacts
```bash
# If using Docker
docker system prune -a --volumes
```

### 4. Database Maintenance
```bash
# Vacuum SQLite databases
for db in data/*.db; do
    sqlite3 "$db" "VACUUM;"
done
```

---

## 🎯 Troubleshooting

### High Disk Usage
1. Check `crew_data/Downloads/` - often the culprit
2. Run `du -sh */ | sort -rh | head -10`
3. Archive old benchmark results
4. Clean virtual environment

### Slow Performance
1. Clear Python cache: `find . -name "__pycache__" -exec rm -rf {} +`
2. Optimize databases: `sqlite3 data/*.db "VACUUM;"`
3. Clear semantic cache: `rm -rf cache/semantic/*`

### Import Errors
1. Ensure using correct import paths (see `.metadata/README.md`)
2. Check for stale `.pyc` files
3. Rebuild if needed: `pip install -e .`

---

## 📊 Space Management

### Current Large Directories
```
1.6G    venv/          # Python environment
96M     crew_data/     # Workspace data  
93M     archive/       # Historical files
27M     src/           # Source code
23M     tests/         # Test suite
```

### Space-Saving Tips
1. **venv/**: Run `optimize_venv.sh --compact`
2. **crew_data/**: Archive old downloads monthly
3. **archive/**: External backup > 1 year old
4. **benchmarks/**: Keep only last 3 months

---

## 🔄 Automation Setup

### Pre-commit Hook
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

### Cron Jobs
```bash
# Add to crontab -e
# Weekly cleanup (Sundays at 2 AM)
0 2 * * 0 cd /home/crew && ./scripts/utilities/maintenance/cleanup_repository.sh

# Monthly archive (1st of month at 3 AM)
0 3 1 * * cd /home/crew && ./scripts/utilities/maintenance/archive_old_files.sh 30
```

---

## 📈 Monitoring

### Check Repository Health
```bash
# Quick health check
echo "=== Repository Health Check ==="
echo "Directories: $(ls -1d */ | wc -l)"
echo "Python files: $(find src -name "*.py" | wc -l)"
echo "Test files: $(find tests -name "test_*.py" | wc -l)"
echo "Total size: $(du -sh . | cut -f1)"
echo ""
echo "=== Large directories ==="
du -sh */ | sort -rh | head -5
```

### Track Growth
```bash
# Weekly size tracking
date >> .metadata/size_tracking.log
du -sh . >> .metadata/size_tracking.log
echo "---" >> .metadata/size_tracking.log
```

---

## 🚨 Emergency Cleanup

If running out of space:
```bash
# 1. Clear all caches
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
rm -rf cache/*

# 2. Archive all old files
./scripts/utilities/maintenance/archive_old_files.sh 7

# 3. Clean venv
./scripts/utilities/maintenance/optimize_venv.sh --compact

# 4. Remove old downloads
rm -rf crew_data/Downloads/*

# 5. Check what's left
du -sh */ | sort -rh | head -10
```

---

## 📝 Best Practices

1. **Run weekly cleanup** - Prevents accumulation
2. **Archive before delete** - Preserve history
3. **Monitor growth** - Track size trends
4. **Document changes** - Update `.metadata/` guides
5. **Test after cleanup** - Ensure nothing breaks

---

## 🔗 Related Documentation

- [README.md](.metadata/README.md) - Navigation guide
- [DIRECTORY_INDEX.md](.metadata/DIRECTORY_INDEX.md) - Structure map
- [FINAL_CLEANUP_SUMMARY.md](.metadata/FINAL_CLEANUP_SUMMARY.md) - Cleanup details

---

**Remember:** A clean repository is a happy repository! 🎉

