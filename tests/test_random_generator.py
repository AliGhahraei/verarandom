from typing import Callable
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
def patch_vera() -> VeraFactory:
    def _patch_vera(quota: int = MAX_QUOTA):
        _patch_response(QUOTA_URL, body=str(quota))
        return VeraRandom()

    return _patch_vera


def _patch_int_response(body: str, **kwargs):
    _patch_response(INTEGER_URL, body=body, **kwargs)


def _patch_response(url: str, method: str=responses.GET, **kwargs):
    responses.add(method, url, **kwargs)


@responses.activate
def test_valid_quota(patch_vera: VeraFactory):
    patch_vera().check_quota()


@responses.activate
def test_valid_quota_at_limit(patch_vera: VeraFactory):
    patch_vera(QUOTA_LIMIT).check_quota()


@responses.activate
def test_invalid_quota_below_limit(patch_vera: VeraFactory):
    vera = patch_vera(QUOTA_LIMIT - 1)
    assert_that(vera.check_quota).raises(RandomOrgQuotaExceeded)


@responses.activate
def test_invalid_quota_response(patch_vera: VeraFactory):
    _patch_response(QUOTA_URL, status=500)
    assert_that(patch_vera).raises(HTTPError)


@mark.parametrize('response', [('17',)])
@mark.xfail
@responses.activate
def test_random(patch_vera: VeraFactory, response: str):
    vera = patch_vera()
    _patch_int_response(response)

    with mock.patch.object(vera, 'check_quota') as check_quota:
        assert_that(patch_vera().random()).is_greater_than_or_equal_to(0).\
            is_less_than(1)

        check_quota.assert_called_once()


@mark.parametrize('lower, upper, response', [(1, 20, '17')])
@responses.activate
def test_randint(patch_vera: VeraFactory, lower: int, upper: int, response: str):
    vera = patch_vera()
    _patch_int_response(response)

    with mock.patch.object(vera, 'check_quota') as check_quota:
        assert_that(vera.randint(lower, upper)).is_greater_than_or_equal_to(lower).\
            is_less_than_or_equal_to(upper)

        check_quota.assert_called_once()


@mark.parametrize('lower, upper, n, response', [(1, 3, 5, '3\n3\n1\n2\n1')])
@responses.activate
def test_randints(patch_vera: VeraFactory, lower: int, upper: int, n: int, response: str):
    vera = patch_vera()
    _patch_int_response(response)

    with mock.patch.object(vera, 'check_quota') as check_quota:
        for random in vera.randints(lower, upper, n):
            assert_that(random).is_greater_than_or_equal_to(lower).is_less_than_or_equal_to(upper)

        check_quota.assert_called_once()
