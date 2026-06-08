"""Этот модуль является плагином для пайтеста для запуска инфраструктуры.
pytest_load_initial_conftests хук позволяет загружать инфраструктуру до запуска основного conftest.
Это сделано для того, чтобы запустить всю инфраструктуру, пробросить необходимые переменные окружения
и уже после этого инициализировать все тесты (т.к. они импортируют объекты, которые зависят от переменных окружений
и должны подтянуться позже этого модуля)
"""  # noqa: E501

import os

import pytest
from testcontainers.postgres import PostgresContainer


def pytest_load_initial_conftests(
    early_config: pytest.Config,
    parser: pytest.Parser,
    args: list[str],
) -> None:
    # os.environ берётся из pytest-env
    container = PostgresContainer(
        "postgres:13",
        username=os.environ.get("POSTGRES_USER"),
        dbname=os.environ.get("POSTGRES_DB"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        driver="postgresql+asyncpg",
    )
    container.start()

    # динамически записываем хост и порт т.к. они генерируются в рантайме
    os.environ["POSTGRES_HOST"] = container.get_container_host_ip()
    os.environ["POSTGRES_PORT"] = str(container.get_exposed_port(5432))

    early_config.pg_container = container


def pytest_unconfigure(config: pytest.Config) -> None:
    config.pg_container.stop()  # останавливаем после всех тестов
