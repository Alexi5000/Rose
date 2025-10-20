# Data Persistence and Backup Guide

This document explains how to configure data persistence for Rose the Healer Shaman application, including Railway volume setup, automatic backups, and disaster recovery procedures.

## Overview

The application stores two types of persistent data:

1. **Short-term Memory**: SQLite database (`/app/data/memory.db`) containing conversation state and checkpoints
2. **Backups**: Automated daily backups of the SQLite database (`/app/data/backups/`)

## Railway Persistent Volume Setup

Railway uses ephemeral storage by default, meaning all data is lost when the service restarts. To persist data across deployments, you must configure a persistent volume.

### Step 1: Create a Volume in Railway Dashboard

1. Open your Railway project dashboard
2. Navigate to your service (Rose the Healer Shaman)
3. Click on the **"Variables"** tab
4. Scroll down to **"Volumes"** section
5. Click **"+ New Volume"**
6. Configure the volume:
   - **Mount Path**: `/app/data`
   - **Size**: 1GB (minimum recommended, adjust based on usage)
7. Click **"Add"** to create the volume

### Step 2: Verify Volume Configuration

After creating the volume:

1. Redeploy your service to apply the volume mount
2. Check the deployment logs to ensure the volume is mounted correctly
3. Look for log messages like: `"Background scheduler started - audio cleanup and database backup jobs scheduled"`

### Step 3: Test Data Persistence

To verify data persists across deployments:

1. Start a conversation with Rose and create some session data
2. Trigger a manual redeploy from Railway dashboard
3. After redeployment, check if your session data is still available
4. Verify backup files exist in `/app/data/backups/`

## Automatic Backup System

The application includes an automated backup system that runs daily.

### Backup Schedule

- **Frequency**: Daily at 2:00 AM (server time)
- **Retention**: 7 days (7 most recent backups are kept)
- **Location**: `/app/data/backups/memory_backup_YYYYMMDD_HHMMSS.db`

### Backup Features

1. **Automatic Cleanup**: Old backups beyond the 7-day retention period are automatically deleted
2. **Timestamped Files**: Each backup includes a timestamp for easy identification
3. **Non-Blocking**: Backups run in the background without affecting service availability
4. **Error Handling**: Backup failures are logged but don't crash the application

### Manual Backup

To create a manual backup, you can use the Railway CLI or SSH into your container:

```bash
# Using Railway CLI
railway run python -c "from ai_companion.core.backup import backup_manager; backup_manager.backup_database()"
```

## Automatic Audio File Cleanup

Temporary audio files (TTS responses) are automatically cleaned up to prevent disk space exhaustion.

### Cleanup Schedule

- **Frequency**: Every hour
- **Retention**: 24 hours
- **Location**: `/tmp/rose_audio/*.mp3`

### How It Works

1. The scheduler runs `cleanup_old_audio_files()` every hour
2. Files older than 24 hours are automatically deleted
3. Active audio files (recently generated) are preserved
4. Cleanup failures are logged but don't affect service

## Disaster Recovery

### Restoring from Backup

If you need to restore the database from a backup:

1. **Identify the backup file** you want to restore:
   ```bash
   ls -lh /app/data/backups/
   ```

2. **Stop the application** (to prevent database corruption):
   ```bash
   # In Railway dashboard, temporarily stop the service
   ```

3. **Restore the backup**:
   ```bash
   cp /app/data/backups/memory_backup_YYYYMMDD_HHMMSS.db /app/data/memory.db
   ```

4. **Restart the application** from Railway dashboard

### Backup Download (for off-site storage)

To download backups for off-site storage:

1. **Using Railway CLI**:
   ```bash
   railway run cat /app/data/backups/memory_backup_YYYYMMDD_HHMMSS.db > local_backup.db
   ```

2. **Using Railway Dashboard**:
   - Use the "Shell" feature to access the container
   - Copy backup files to a temporary location
   - Download via Railway's file browser (if available)

### Database Corruption Recovery

If the database becomes corrupted:

1. Check the logs for error messages
2. Restore from the most recent backup (see above)
3. If no backups are available, the application will create a new database automatically
4. Note: Restoring from backup will lose any data created after the backup timestamp

## Monitoring and Maintenance

### Check Backup Status

Monitor backup creation in the application logs:

```
INFO - Database backup created: /app/data/backups/memory_backup_20241020_020000.db
INFO - Removed old backup: memory_backup_20241013_020000.db
```

### Check Disk Usage

Monitor disk usage to ensure the volume has sufficient space:

```bash
# Using Railway CLI
railway run df -h /app/data
```

### Adjust Backup Retention

To change the backup retention period, modify the scheduler configuration in `src/ai_companion/interfaces/web/app.py`:

```python
scheduler.add_job(
    backup_manager.backup_database,
    'cron',
    hour=2,
    minute=0,
    args=[14],  # Change to 14 days retention
    id='database_backup',
    name='Daily database backup',
    replace_existing=True
)
```

## Storage Requirements

### Minimum Recommended Storage

- **Volume Size**: 1GB minimum
- **Expected Growth**: ~10-50MB per 1000 conversations
- **Backup Storage**: ~7x database size (for 7-day retention)

### Storage Optimization

1. **Adjust backup retention**: Reduce from 7 days to 3 days if storage is limited
2. **Monitor session cleanup**: Old sessions are not automatically deleted (future enhancement)
3. **Audio cleanup**: Temporary audio files are cleaned up automatically (no action needed)

## Troubleshooting

### Volume Not Mounted

**Symptom**: Data is lost after redeployment

**Solution**:
1. Verify volume is configured in Railway dashboard
2. Check mount path is exactly `/app/data`
3. Redeploy the service after adding the volume

### Backup Failures

**Symptom**: No backup files in `/app/data/backups/`

**Solution**:
1. Check application logs for backup errors
2. Verify `/app/data/backups/` directory exists and is writable
3. Ensure sufficient disk space is available
4. Check scheduler is running (look for startup log message)

### Disk Space Exhaustion

**Symptom**: Application crashes or fails to write data

**Solution**:
1. Increase Railway volume size
2. Reduce backup retention period
3. Manually delete old backups if needed
4. Check for orphaned audio files in `/tmp/rose_audio/`

## Best Practices

1. **Monitor Disk Usage**: Regularly check disk usage to prevent exhaustion
2. **Test Backups**: Periodically test backup restoration to ensure they work
3. **Off-site Backups**: Download critical backups for off-site storage
4. **Volume Sizing**: Start with 1GB and increase based on actual usage
5. **Log Monitoring**: Watch logs for backup and cleanup job execution

## Future Enhancements

Planned improvements for data persistence:

1. **PostgreSQL Migration**: For better concurrency and horizontal scaling
2. **Session Cleanup**: Automatic deletion of sessions older than 30-90 days
3. **Backup Compression**: Compress backups to save storage space
4. **Cloud Backup Integration**: Automatic upload to S3/GCS for off-site storage
5. **Backup Verification**: Automated integrity checks for backup files
