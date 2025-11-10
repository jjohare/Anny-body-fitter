"""Database service for managing connections and operations."""

import aiosqlite
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database connections and operations."""

    def __init__(self, db_path: str = "data/anny_fitter.db"):
        """
        Initialize database service.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Initialize database and create tables."""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row

        # Create tables
        await self._create_tables()

        logger.info(f"Database initialized at {self.db_path}")

    async def _create_tables(self):
        """Create database tables if they don't exist."""
        async with self.connection.cursor() as cursor:
            # Subjects table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    height_cm REAL,
                    weight_kg REAL,
                    notes TEXT,
                    photo_count INTEGER DEFAULT 0,
                    has_fitted_model BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP
                )
            """)

            # Photos table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS photos (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    photo_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    width_px INTEGER NOT NULL,
                    height_px INTEGER NOT NULL,
                    camera_height_cm REAL,
                    distance_cm REAL,
                    notes TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                )
            """)

            # Fitting tasks table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS fitting_tasks (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    task_id TEXT,
                    optimization_iterations INTEGER,
                    use_shape_prior BOOLEAN,
                    use_pose_prior BOOLEAN,
                    lambda_shape REAL,
                    lambda_pose REAL,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                )
            """)

            # Model parameters table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_parameters (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL UNIQUE,
                    shape_params TEXT NOT NULL,
                    pose_params TEXT NOT NULL,
                    global_rotation TEXT NOT NULL,
                    global_translation TEXT NOT NULL,
                    num_vertices INTEGER NOT NULL,
                    num_faces INTEGER NOT NULL,
                    final_loss REAL,
                    iterations_completed INTEGER,
                    convergence_achieved BOOLEAN,
                    processing_time_seconds REAL,
                    photo_reprojection_error REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                )
            """)

            # Metrics table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    accuracy_score REAL,
                    precision_score REAL,
                    recall_score REAL,
                    f1_score REAL,
                    mean_error_cm REAL,
                    max_error_cm REAL,
                    ground_truth_available BOOLEAN NOT NULL,
                    validation_method TEXT NOT NULL,
                    notes TEXT,
                    custom_metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                )
            """)

            # Create indexes
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_subjects_user ON subjects(user_id)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_photos_subject ON photos(subject_id)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_fitting_subject ON fitting_tasks(subject_id)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_subject ON metrics(subject_id)")

            await self.connection.commit()

    async def close(self):
        """Close database connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")

    async def execute(self, query: str, params: tuple = ()):
        """Execute a query."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            await self.connection.commit()
            return cursor

    async def fetch_one(self, query: str, params: tuple = ()):
        """Fetch one row."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchone()

    async def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all rows."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchall()
