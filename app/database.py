"""Setup database connection"""

from sqlalchemy.orm.query import Query
from sqlmodel import create_engine, Session, SQLModel
from sqlmodel.orm.session import Result


from app.settings import LOGGER, SQLALCHEMY_DATABASE_URI


ENGINE = create_engine(SQLALCHEMY_DATABASE_URI)


def init_db():
    """Create all tables in the database"""
    SQLModel.metadata.create_all(ENGINE)


def clear_db():
    """Clear all tables in the database"""
    SQLModel.metadata.drop_all(ENGINE)


class SessionManager:  # pylint: disable=too-few-public-methods
    """A singleton data class holding the active database session for use across the app."""

    session: Session | None = None


def get_session():
    """
    Get the database session
    """
    with Session(ENGINE) as session:
        SessionManager.session = session
        yield session
        SessionManager.session = None


class BaseModel(SQLModel):
    """Base model for sql tables which implements useful methods for interacting with the database."""

    @staticmethod
    def exec(statement) -> Result:
        """Executes a SQLAlchemy statement on a database session, and returns the result.

        Args:
            statement (Select): A SQLModel Select statement

        Returns:
            (Result, None): Results from the database query, or None if it fails
        """
        try:
            result = SessionManager.session.exec(statement)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error('Executing database statement failed.', exc_info=1)
            SessionManager.session.rollback()
            raise exc
        return result

    @classmethod
    def query(cls) -> Query:
        """Returns a Query object to preform actions on.

        Returns:
            Query: A SQLAlchemy Query object
        """
        return SessionManager.session.query(cls)

    def save(self, commit: bool = True):
        """Saves an object to the database and returns the saved object.

        Args:
            commit (bool, optional): Choose to wait to add to database for bulk inserts. Defaults to True.

        Returns:
            BaseModel: An instance of the saved model
        """
        SessionManager.session.add(self)
        if commit:
            BaseModel.commit()
        SessionManager.session.refresh(self)  # this is required i guess
        return self

    @staticmethod
    def commit():
        """Commits any staged changes to the database"""
        SessionManager.session.commit()

    @classmethod
    def get_all(cls):
        """
        Get all entries

        Returns:
            list[cls]: A list of all entries of this type from the database.
        """
        return cls.query().all()
