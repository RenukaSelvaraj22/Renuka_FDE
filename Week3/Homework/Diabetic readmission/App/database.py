import psycopg
from psycopg.rows import dict_row
from .config import get_database_url
from .errors import DatabaseUnavailableError

def get_connection() -> psycopg.Connection:
    """Open a connection returning dict rows. Use as `with get_connection() as conn:` (commits, then closes)."""
    try: return psycopg.connect(get_database_url(), row_factory=dict_row)
    except psycopg.OperationalError: raise DatabaseUnavailableError("Could not connect to the database.") from None
