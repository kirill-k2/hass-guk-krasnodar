class SessionAPIException(Exception):
    """Базовый класс ошибок"""


class ResponseError(SessionAPIException):
    """Ошибка удаленного сервера"""


class EmptyResponse(SessionAPIException):
    """Ошибка - пустой ответ удаленного сервера"""


class ResponseTimeout(SessionAPIException):
    """Ошибка - таймаут ответа сервера"""


class LoginError(SessionAPIException):
    """Ошибка при попытке логина"""


class AccessDenied(SessionAPIException):
    """Ошибка при попытке логина"""


class NoAuthError(SessionAPIException):
    """Ошибка авторизации"""


class InvalidValue(SessionAPIException):
    """Неверное значение"""
