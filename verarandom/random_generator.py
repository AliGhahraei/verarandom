from random import Random

from requests import get


RANDOM_ORG_URL = 'https://www.random.org'
QUOTA_URL = f'{RANDOM_ORG_URL}/quota'

QUOTA_LIMIT = 0
MAX_QUOTA = 1_000_000

FORMAT = 'format'
PLAIN_FORMAT = 'plain'

random_calls = 0


class RandomOrgQuotaExceeded(Exception):
    """ IP has exceeded bit quota and should not be allowed to make further requests. """


class VeraRandom(Random):
    """ Random number generator powered by random.org """
    def __init__(self):
        self.remaining_quota = get(QUOTA_URL, params={FORMAT: PLAIN_FORMAT})
        self.remaining_quota.raise_for_status()
        super().__init__()

    def check_quota(self):
        """ Verify the user's IP can make requests. Should be called before generating numbers. """
        if int(self.remaining_quota.text) < QUOTA_LIMIT:
            raise RandomOrgQuotaExceeded

    def random(self) -> float:
        raise NotImplementedError

    def randint(self, a: int, b: int, n: int=1):
        raise NotImplementedError
