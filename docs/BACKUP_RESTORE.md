# Backup & Restoration Procedures

To backup user database and uploads:
```bash
tar -cvzf jarvis_backup.tar.gz ./data/uploads jarvis.db
```
To restore:
```bash
tar -xvzf jarvis_backup.tar.gz
```
