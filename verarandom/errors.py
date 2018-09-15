class VeraRandomError(Exception):
    """ Base exception class for the whole package. """


class HTTPError(VeraRandomError):
    """ An HTTP error occured """


class BitQuotaExceeded(VeraRandomError):
    """ IP has exceeded bit quota and is not allowed to make further requests. """


class RandomRequestFieldError(VeraRandomError, ValueError):
    """ At least one of the request's fields is invalid """


class NoRandomNumbersRequested(RandomRequestFieldError):
    """ Attempted to request 0 numbers """


class TooManyRandomNumbersRequested(RandomRequestFieldError):
    """ Attempted to request too many numbers for the service's API """


class RandomNumberLimitTooLarge(RandomRequestFieldError):
    """ Max random number requested is too large for the service's API """


class RandomNumberLimitTooSmall(RandomRequestFieldError):
    """ Min random number requested is too small for the service's API """
