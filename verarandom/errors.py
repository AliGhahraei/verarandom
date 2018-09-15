class VeraRandomError(Exception):
    """ Base exception class """


class BitQuotaExceeded(VeraRandomError):
    """ IP has exceeded bit quota and should not be allowed to make further requests. """


class RandomRequestFieldError(VeraRandomError, ValueError):
    """ At least one of the request's fields is invalid """


class NoRandomNumbersRequested(RandomRequestFieldError):
    """ Attempted to request 0 numbers """


class TooManyRandomNumbersRequested(RandomRequestFieldError):
    """ Attempted to request too many numbers to the generator's API """


class RandomNumberLimitTooLarge(RandomRequestFieldError):
    """ Max random number requested is too large for the generator's API """


class RandomNumberLimitTooSmall(RandomRequestFieldError):
    """ Min random number requested is too small for the generator's API """
