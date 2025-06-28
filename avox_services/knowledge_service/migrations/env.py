import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import text, engine_from_config, pool

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Импорт моделей и базы
from knowledge_service.app.models import Base

# Метаданные для Alembic
target_metadata = Base.metadata

# Alembic Config object
config = context.config

# Чтение логгера из файла конфигурации
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Фильтр по схеме
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return object.schema == "kno"
    return True

def run_migrations_offline():
    """Офлайн режим — используется для генерации SQL-скриптов"""
    url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Онлайн режим — подключение к БД"""
    url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    connectable = engine_from_config(
        configuration= {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS kno"))
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
