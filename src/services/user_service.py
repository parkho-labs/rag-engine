import uuid
import logging
from typing import Optional, Dict, Any
from database.connection import db_connection
from services.minio_service import minio_service

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        self.init_schema()

    def init_schema(self):
        try:
            users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                email VARCHAR(255),
                name VARCHAR(255),
                is_anonymous BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            user_files_table = """
            CREATE TABLE IF NOT EXISTS user_files (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255) NOT NULL REFERENCES users(id),
                filename VARCHAR(500) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                file_size BIGINT NOT NULL,
                minio_path VARCHAR(1000) NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            indexes = """
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_is_anonymous ON users(is_anonymous);
            CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON user_files(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_files_file_type ON user_files(file_type);
            CREATE INDEX IF NOT EXISTS idx_user_files_upload_date ON user_files(upload_date);
            """

            db_connection.execute_query(users_table)
            db_connection.execute_query(user_files_table)
            db_connection.execute_query(indexes)

            logger.info("User schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize user schema: {e}")

    def generate_anonymous_user_id(self) -> str:
        return f"anonymous_{str(uuid.uuid4())[:8]}"

    def create_anonymous_user(self) -> str:
        try:
            user_id = self.generate_anonymous_user_id()
            query = "INSERT INTO users (id, is_anonymous) VALUES (%s, %s)"
            db_connection.execute_query(query, (user_id, True))
            logger.info(f"Created anonymous user: {user_id}")
            return user_id
        except Exception as e:
            logger.error(f"Failed to create anonymous user: {e}")
            raise e

    def register_user(self, user_id: str, email: str, name: str, anonymous_session_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            if self.user_exists(user_id):
                return {"status": "SUCCESS", "message": "User already exists", "user_id": user_id}

            query = "INSERT INTO users (id, email, name, is_anonymous) VALUES (%s, %s, %s, %s)"
            db_connection.execute_query(query, (user_id, email, name, False))

            if anonymous_session_id and self.user_exists(anonymous_session_id):
                self.migrate_anonymous_data(anonymous_session_id, user_id)

            logger.info(f"Registered user: {user_id}")
            return {"status": "SUCCESS", "message": "User registered successfully", "user_id": user_id}

        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            return {"status": "FAILURE", "message": str(e)}

    def user_exists(self, user_id: str) -> bool:
        try:
            query = "SELECT id FROM users WHERE id = %s"
            result = db_connection.execute_one(query, (user_id,))
            return result is not None
        except Exception:
            return False

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            query = "SELECT id, email, name, is_anonymous, created_at FROM users WHERE id = %s"
            result = db_connection.execute_one(query, (user_id,))
            if result:
                return {
                    "id": result[0],
                    "email": result[1],
                    "name": result[2],
                    "is_anonymous": result[3],
                    "created_at": result[4].isoformat() if result[4] else None
                }
            return None
        except Exception:
            return None

    def migrate_anonymous_data(self, from_user_id: str, to_user_id: str):
        try:
            logger.info(f"Migrating data from {from_user_id} to {to_user_id}")

            self.migrate_user_files(from_user_id, to_user_id)

            query = "DELETE FROM users WHERE id = %s"
            db_connection.execute_query(query, (from_user_id,))

            logger.info(f"Migration completed from {from_user_id} to {to_user_id}")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise e

    def migrate_user_files(self, from_user_id: str, to_user_id: str):
        try:
            query = "SELECT id, minio_path FROM user_files WHERE user_id = %s"
            files = db_connection.execute_query(query, (from_user_id,))

            for file_record in files:
                file_id, old_minio_path = file_record
                bucket_name, old_object_name = old_minio_path.split('/', 1)

                filename = old_object_name.split('/')[-1]
                new_object_name = f"{to_user_id}/{filename}"
                new_minio_path = f"{bucket_name}/{new_object_name}"

                file_data = minio_service.download_file(bucket_name, old_object_name)
                if file_data:
                    import io
                    file_stream = io.BytesIO(file_data)
                    minio_service.upload_file(bucket_name, new_object_name, file_stream, len(file_data))
                    minio_service.delete_file(bucket_name, old_object_name)

                    update_query = "UPDATE user_files SET user_id = %s, minio_path = %s WHERE id = %s"
                    db_connection.execute_query(update_query, (to_user_id, new_minio_path, file_id))

            logger.info(f"Migrated {len(files)} files from {from_user_id} to {to_user_id}")

        except Exception as e:
            logger.error(f"File migration failed: {e}")
            raise e

    def cleanup_anonymous_users(self, days_old: int = 30):
        try:
            query = """
            DELETE FROM users
            WHERE is_anonymous = true
            AND created_at < NOW() - INTERVAL '%s days'
            """
            result = db_connection.execute_query(query, (days_old,))
            logger.info(f"Cleaned up {result} anonymous users older than {days_old} days")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


user_service = UserService()