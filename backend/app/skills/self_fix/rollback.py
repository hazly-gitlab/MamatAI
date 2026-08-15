import os
import shutil
import logging

logger = logging.getLogger("jarvis_rollback")

class BackupManager:
    @staticmethod
    def create_backup(filepath: str) -> bool:
        """Creates a backup file of the production file before modifying it."""
        if not os.path.exists(filepath):
            logger.error(f"Cannot backup non-existent file: {filepath}")
            return False

        backup_path = f"{filepath}.bak"
        try:
            shutil.copy2(filepath, backup_path)
            logger.info(f"Created rollback backup for {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return False

    @staticmethod
    def restore_backup(filepath: str) -> bool:
        """Restores the backup file, rolling back any applied modifications."""
        backup_path = f"{filepath}.bak"
        if not os.path.exists(backup_path):
            logger.error(f"No backup file found to rollback: {backup_path}")
            return False

        try:
            shutil.move(backup_path, filepath)
            logger.info(f"Successfully rolled back to original file state for {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {str(e)}")
            return False

    @staticmethod
    def delete_backup(filepath: str):
        """Removes the backup file once production patch is fully validated."""
        backup_path = f"{filepath}.bak"
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
                logger.info(f"Cleaned up backup file: {backup_path}")
            except Exception:
                pass
