from typing import Callable

import responses
from assertpy import assert_that
from pytest import fixture, mark
from requests import HTTPError

from verarandom.random_generator import (
    VeraRandom, QUOTA_URL, QUOTA_LIMIT, MAX_QUOTA, RandomOrgQuotaExceeded, INTEGER_URL
)


VeraFactory = Callable[..., VeraRandom]


@fixture
def mock_vera() -> VeraFactory:
    def _mock_vera(quota: int = MAX_QUOTA):
        _mock_response(QUOTA_URL, body=str(quota))
        return VeraRandom()

    return _mock_vera


@responses.activate
def test_valid_quota(mock_vera: VeraFactory):
    mock_vera().check_quota()


@responses.activate
def test_valid_quota_at_limit(mock_vera: VeraFactory):
    mock_vera(QUOTA_LIMIT).check_quota()


@responses.activate
def test_invalid_quota_below_limit(mock_vera: VeraFactory):
    mock = mock_vera(QUOTA_LIMIT - 1)
    assert_that(mock.check_quota).raises(RandomOrgQuotaExceeded)


@responses.activate
def test_invalid_quota_response(mock_vera: VeraFactory):
    _mock_response(QUOTA_URL, status=500)
    assert_that(mock_vera).raises(HTTPError)


@mark.xfail
@responses.activate
def test_random(mock_vera: VeraFactory):
    assert_that(mock_vera().random()).is_greater_than_or_equal_to(0).is_less_than(1)


@mark.parametrize('lower, upper, response', [(1, 20, '17')])
@responses.activate
def test_randint(mock_vera: VeraFactory, lower: int, upper: int, response: str):
    _mock_int_response(response)
    assert_that(mock_vera().randint(lower, upper)).is_greater_than_or_equal_to(lower).\
        is_less_than_or_equal_to(upper)


@mark.parametrize('lower, upper, n, response', [(1, 3, 5, '3\n3\n1\n2\n1')])
@responses.activate
def test_randints(mock_vera: VeraFactory, lower: int, upper: int, n: int, response: str):
    _mock_int_response(response)
    for random in mock_vera().randints(lower, upper, n):
        assert_that(random).is_greater_than_or_equal_to(lower).is_less_than_or_equal_to(upper)


def _mock_response(url: str, method: str=responses.GET, **kwargs):
    responses.add(method, url, **kwargs)


def _mock_int_response(body: str, **kwargs):
    _mock_response(INTEGER_URL, body=body, **kwargs)
