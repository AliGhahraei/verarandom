""" Old client for RandomOrg's API. """
from enum import Enum, IntEnum
from typing import List, Dict, Optional, Union

from requests import get

from verarandom import VeraRandomQuota, RandomConfig


RANDOM_ORG_URL = 'https://www.random.org'
QUOTA_URL = f'{RANDOM_ORG_URL}/quota'
INTEGER_URL = f'{RANDOM_ORG_URL}/integers'

MAX_QUOTA = 1_000_000

MAX_INTEGER_LIMIT = int(1e9)
MIN_INTEGER_LIMIT = int(-1e9)
MAX_NUMBER_OF_INTEGERS = int(1e4)

FORMAT = 'format'
PLAIN_FORMAT = 'plain'


class _RandintsToFloatOptions(IntEnum):
    RANDINTS_QUANTITY = 3
    RANDINTS_NUMBER_OF_DIGITS = 5


class _RandintRequestFields(Enum):
    RANDOMIZATION = 'rnd'
    TRULY_RANDOM = 'new'
    BASE = 'base'
    BASE_10 = '10'
    NUM = 'num'
    MIN = 'min'
    MAX = 'max'
    COL = 'col'


class RandomOrg(VeraRandomQuota):
    """ `<http://random.org/>`_ number generator.

     NOTE: this class assumes it's the only one talking to the server when calculating its quota.
     """
    def __init__(self, initial_quota: Optional[int] = None):
        # noinspection PyArgumentList
        config = RandomConfig(MAX_INTEGER_LIMIT, MIN_INTEGER_LIMIT, MAX_NUMBER_OF_INTEGERS, 0)
        super().__init__(config, initial_quota)

    def random(self, n: Optional[int] = None) -> Union[List[float], float]:
        """ Generate random float(s) by using integers as fractional part.

        random.org's API doesn't offer floats, but a sequence of integers can emulate this:

        [06357, 114, 0210] => 0.06357_00114_00210
        """
        randoms = []
        n_or_default = 1 if n is None else n

        for _ in range(n_or_default):
            number_of_digits = _RandintsToFloatOptions.RANDINTS_NUMBER_OF_DIGITS.value
            max_int = int('9' * number_of_digits)

            randints = self.randint(0, max_int, _RandintsToFloatOptions.RANDINTS_QUANTITY.value)
            zero_padded_ints = (str(randint).zfill(number_of_digits) for randint in randints)
            random = float(f"0.{''.join(zero_padded_ints)}")
            randoms.append(random)

        return randoms if n else randoms[0]

    def _request_quota(self) -> int:
        return int(self._make_plain_text_request(QUOTA_URL))

    def _request_randints(self, a: int, b: int, n: int) -> List[int]:
        params = self._create_randint_request_params(a, b, n)
        numbers_as_string = self._make_plain_text_request(INTEGER_URL, kwargs=params)
        return [int(random) for random in numbers_as_string.splitlines()]

    @staticmethod
    def _create_randint_request_params(a: int, b: int, n: int) -> Dict:
        return {_RandintRequestFields.RANDOMIZATION.value: _RandintRequestFields.TRULY_RANDOM.value,
                _RandintRequestFields.BASE.value: _RandintRequestFields.BASE_10.value,
                _RandintRequestFields.MIN.value: a, _RandintRequestFields.MAX.value: b,
                _RandintRequestFields.NUM.value: n, _RandintRequestFields.COL.value: 1}

    @staticmethod
    def _make_plain_text_request(url: str, **kwargs) -> str:
        response = get(url, params={FORMAT: PLAIN_FORMAT, **kwargs})
        response.raise_for_status()

        return response.text

    def _get_bits_spent(self, integers: List[int]):
        return sum(integer.bit_length() for integer in integers)

    def _request_randoms(self, _: int):
        raise NotImplementedError
