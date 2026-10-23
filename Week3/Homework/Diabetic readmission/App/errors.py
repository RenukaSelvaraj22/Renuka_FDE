class AppError(Exception):
    """Base class for errors the API/importer turns into clean messages."""

class ConfigurationError(AppError): pass

class DatabaseUnavailableError(AppError): pass

class NotFoundError(AppError): pass

class DuplicateEncounterError(AppError): pass

class ImportDataError(AppError): pass
