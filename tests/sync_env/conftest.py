import logging
from datetime import datetime

import pytest
from sqlalchemy import DateTime, Engine, Integer, String, Text, create_engine, func
from sqlalchemy.orm import (
    Mapped,
    Session,
    declarative_base,
    mapped_column,
    scoped_session,
    sessionmaker,
)

from src import init_manager, transaction_context

ORMBase = declarative_base()


def db_startup(sync_engine_: Engine):
    # db init
    with sync_engine_.begin() as conn:
        ORMBase.metadata.create_all(conn)

    logging.info('[sync] DB initialized')


def db_shutdown(sync_engine_: Engine):
    # db close
    sync_engine_.dispose()
    logging.info('DB disposed')


@pytest.fixture(scope='module', autouse=True)
def sync_engine_() -> Engine:
    DB_URL = 'sqlite:///:memory:'
    sync_engine_ = create_engine(DB_URL, echo=False)
    db_startup(sync_engine_)
    return sync_engine_


@pytest.fixture(scope='function', autouse=True)
def session_factory_(sync_engine_: Engine) -> sessionmaker:
    session_factory = sessionmaker(sync_engine_, expire_on_commit=False)
    return session_factory


@pytest.fixture(scope='function', autouse=True)
def scoped_session_(session_factory_) -> scoped_session:
    # 새로운 세션 시작
    scoped_session_ = scoped_session(session_factory_)

    return scoped_session_


@pytest.fixture(scope='function', autouse=True)
def session_start_up(scoped_session_: scoped_session) -> None:
    init_manager(scoped_session_)
    logging.info('[sync] Session initialized')


@pytest.fixture(scope='function', autouse=True)
def transaction_sync(session_factory_, session_start_up) -> Session:
    scoped_session_ = scoped_session(session_factory_)

    sess = scoped_session_()
    transaction_context.set(sess)

    return sess


class Post(ORMBase):
    __tablename__ = 'post_sync'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

