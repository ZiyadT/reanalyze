import os
from pathlib import Path
import unittest
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
BACKEND_DIR = Path(__file__).resolve().parents[1]


@unittest.skipUnless(DATABASE_URL, "Set TEST_DATABASE_URL to a PostgreSQL test database")
class EmbeddingConfigurationMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(DATABASE_URL)
        cls.connection = cls.engine.connect()
        cls.schema = f"test_embedding_{uuid4().hex}"
        try:
            cls.connection.execute(text(f'CREATE SCHEMA "{cls.schema}"'))
            cls.connection.execute(text(f'SET search_path TO "{cls.schema}"'))
            cls.connection.commit()
            cls.config = Config(str(BACKEND_DIR / "alembic.ini"))
            cls.config.attributes["connection"] = cls.connection
            command.upgrade(cls.config, "head")
        except Exception:
            cls.connection.rollback()
            cls.connection.execute(text(f'DROP SCHEMA IF EXISTS "{cls.schema}" CASCADE'))
            cls.connection.commit()
            cls.connection.close()
            cls.engine.dispose()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.connection.rollback()
        cls.connection.execute(text(f'DROP SCHEMA "{cls.schema}" CASCADE'))
        cls.connection.commit()
        cls.connection.close()
        cls.engine.dispose()

    def setUp(self):
        self.transaction = self.connection.begin()

    def tearDown(self):
        self.transaction.rollback()

    def insert_configuration(self, **overrides):
        values = {
            "provider": "openai",
            "model_name": "example-model",
            "model_version": None,
            "dimensions": 1536,
            "normalization": "l2",
            "similarity_metric": "cosine",
        }
        values.update(overrides)
        return self.connection.execute(
            text(
                """
                INSERT INTO embedding_configurations
                    (provider, model_name, model_version, dimensions,
                     normalization, similarity_metric)
                VALUES
                    (:provider, :model_name, :model_version, :dimensions,
                     :normalization, :similarity_metric)
                RETURNING id, model_version, created_at
                """
            ),
            values,
        ).one()

    def test_valid_configuration_has_timezone_aware_timestamp(self):
        row = self.insert_configuration()
        self.assertIsNone(row.model_version)
        self.assertIsNotNone(row.created_at.tzinfo)
        self.insert_configuration(normalization="none", similarity_metric="dot_product")
        self.insert_configuration(similarity_metric="euclidean", model_version="v1")

    def test_invalid_values_are_rejected_by_database(self):
        invalid_values = [
            {"provider": ""},
            {"provider": " \t\n"},
            {"model_name": ""},
            {"model_name": "\t"},
            {"dimensions": 0},
            {"dimensions": -1},
            {"normalization": "invalid"},
            {"similarity_metric": "invalid"},
            {"provider": None},
        ]
        for values in invalid_values:
            with self.subTest(values=values):
                with self.assertRaises(DBAPIError):
                    with self.connection.begin_nested():
                        self.insert_configuration(**values)

    def test_database_rejects_configuration_updates(self):
        row = self.insert_configuration()
        with self.assertRaisesRegex(DBAPIError, "Embedding configurations are immutable"):
            with self.connection.begin_nested():
                self.connection.execute(
                    text(
                        "UPDATE embedding_configurations "
                        "SET dimensions = 768 WHERE id = :id"
                    ),
                    {"id": row.id},
                )
        self.assertEqual(
            self.connection.execute(
                text("SELECT dimensions FROM embedding_configurations WHERE id = :id"),
                {"id": row.id},
            ).scalar_one(),
            1536,
        )

    def test_migration_downgrade_and_reupgrade(self):
        command.downgrade(self.config, "base")
        self.assertIsNone(
            self.connection.execute(
                text("SELECT to_regclass('embedding_configurations')")
            ).scalar_one()
        )
        command.upgrade(self.config, "head")
        row = self.insert_configuration()
        with self.assertRaisesRegex(DBAPIError, "Embedding configurations are immutable"):
            with self.connection.begin_nested():
                self.connection.execute(
                    text("UPDATE embedding_configurations SET provider = 'other' WHERE id = :id"),
                    {"id": row.id},
                )
