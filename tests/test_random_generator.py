from typing import Callable, Any, Iterable
from unittest import mock

import responses
from assertpy import assert_that
from pytest import fixture, mark
from requests import HTTPError

from verarandom.random_generator import (
    VeraRandom, QUOTA_URL, QUOTA_LIMIT, MAX_QUOTA, RandomOrgQuotaExceeded, INTEGER_URL
)


VeraFactory = Callable[..., VeraRandom]


@fixture
def patch_vera_quota() -> VeraFactory:
    def _patch_vera_quota(quota: int = MAX_QUOTA):
        _patch_response(QUOTA_URL, body=str(quota))
        return VeraRandom()

    return _patch_vera_quota


def _patch_int_response(body: str, **kwargs):
    _patch_response(INTEGER_URL, body=body, **kwargs)


def _patch_response(url: str, method: str=responses.GET, **kwargs):
    responses.add(method, url, **kwargs)


@responses.activate
def test_valid_quota(patch_vera_quota: VeraFactory):
    patch_vera_quota().check_quota()


@responses.activate
def test_valid_quota_at_limit(patch_vera_quota: VeraFactory):
    patch_vera_quota(QUOTA_LIMIT).check_quota()


@responses.activate
def test_invalid_quota_below_limit(patch_vera_quota: VeraFactory):
    assert_that(patch_vera_quota(QUOTA_LIMIT - 1).check_quota).raises(RandomOrgQuotaExceeded)


@responses.activate
def test_invalid_quota_response():
    _patch_response(QUOTA_URL, status=500)
    assert_that(VeraRandom).raises(HTTPError)


@mark.parametrize('mock_responses', [('1\n2\n3\n4\n5', '6\n7\n8\n9\n0', '1\n1\n1\n1\n1')])
@mark.xfail
@responses.activate
def test_random(patch_vera_quota: VeraFactory, mock_responses: str):
    assert_rand_call_output(patch_vera_quota(), 'random',
                            mock_responses=mock_responses, output=0.12345_67890_11111)


@mark.parametrize('lower, upper, mock_responses', [(1, 20, ('17',))])
@responses.activate
def test_randint(patch_vera_quota: VeraFactory, lower: int, upper: int, mock_responses: str):
    assert_rand_call_output(patch_vera_quota(), 'randint', lower, upper,
                            mock_responses=mock_responses, output=17)


@mark.parametrize('lower, upper, n, mock_responses', [(1, 3, 5, ('3\n3\n1\n2\n1',))])
@responses.activate
def test_randints(patch_vera_quota: VeraFactory, lower: int, upper: int, n: int,
                  mock_responses: str):
    assert_rand_call_output(patch_vera_quota(), 'randints', lower, upper, n,
                            mock_responses=mock_responses, output=[3, 3, 1, 2, 1])


def assert_rand_call_output(vera: VeraRandom, method: str, *args, mock_responses: Iterable[str],
                            output: Any):
    for mock_response in mock_responses:
        _patch_int_response(mock_response)

    with mock.patch.object(vera, 'check_quota') as check_quota:
        assert_that(getattr(vera, method)(*args)).is_equal_to(output)

        check_quota.assert_called_once()
