from typing import Callable

import responses
from assertpy import assert_that
from pytest import fixture, mark
from requests import HTTPError

from verarandom.random_generator import (
    VeraRandom, QUOTA_URL, QUOTA_LIMIT, MAX_QUOTA, RandomOrgQuotaExceeded
)


VeraFactory = Callable[..., VeraRandom]


@fixture
def mock_vera() -> VeraFactory:
    def _mock_vera(quota: int = MAX_QUOTA):
        _mock_response(QUOTA_URL, body=str(quota))
        return VeraRandom()

    return _mock_vera


@responses.activate
def test_valid_quota(mock_vera):
    mock_vera().check_quota()


@responses.activate
def test_valid_quota_at_limit(mock_vera):
    mock_vera(QUOTA_LIMIT).check_quota()


@responses.activate
def test_invalid_quota_below_limit(mock_vera):
    mock = mock_vera(QUOTA_LIMIT - 1)
    assert_that(mock.check_quota).raises(RandomOrgQuotaExceeded).when_called_with()


@responses.activate
def test_invalid_quota_response(mock_vera):
    _mock_response(QUOTA_URL, status=500)
    assert_that(mock_vera).raises(HTTPError).when_called_with()


@mark.xfail
@responses.activate
def test_random(mock_vera):
    mock_vera().random()


@mark.xfail
@responses.activate
def test_randint(mock_vera):
    mock_vera().randint(1, 20)


def _mock_response(url: str, method: str=responses.GET, **kwargs):
    responses.add(method, url, **kwargs)
