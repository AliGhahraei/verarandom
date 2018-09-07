from typing import Callable, Any, List
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


@mark.xfail
@mark.parametrize('mock_response, output', [('12345\n67890\n11111', 0.12345_67890_11111)])
@responses.activate
def test_random(patch_vera_quota: VeraFactory, mock_response: str, output: float):
    assert_rand_call_output(patch_vera_quota(), 'random',
                            mock_response=mock_response, output=output)


@mark.parametrize('lower, upper, mock_response, output', [(1, 20, '17', 17)])
@responses.activate
def test_randint(patch_vera_quota: VeraFactory, lower: int, upper: int, mock_response: str,
                 output: int):
    assert_rand_call_output(patch_vera_quota(), 'randint', lower, upper,
                            mock_response=mock_response, output=output)


@mark.parametrize('lower, upper, n, mock_response, output',
                  [(1, 3, 5, '3\n3\n1\n2\n1', [3, 3, 1, 2, 1])])
@responses.activate
def test_randints(patch_vera_quota: VeraFactory, lower: int, upper: int, n: int,
                  mock_response: str, output: List[int]):
    assert_rand_call_output(patch_vera_quota(), 'randints', lower, upper, n,
                            mock_response=mock_response, output=output)


def assert_rand_call_output(vera: VeraRandom, method: str, *args, mock_response: str, output: Any):
    _patch_int_response(mock_response)

    with mock.patch.object(vera, 'check_quota') as check_quota:
        assert_that(getattr(vera, method)(*args)).is_equal_to(output)

        check_quota.assert_called_once()
