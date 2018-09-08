from typing import Callable, Any, List
from unittest import mock

import responses
from assertpy import assert_that
from pytest import fixture, mark
from requests import HTTPError

from verarandom.random_generator import (
    VeraRandom, QUOTA_URL, QUOTA_LIMIT, MAX_QUOTA, BitQuotaExceeded, INTEGER_URL,
    MAX_NUMBER_OF_INTEGERS, TooManyRandomNumbersRequested, MAX_INTEGER, RandomNumberTooLarge,
    MIN_INTEGER, RandomNumberTooSmall)


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
    assert_that(patch_vera_quota(QUOTA_LIMIT - 1).check_quota).raises(BitQuotaExceeded)


@responses.activate
def test_invalid_quota_response():
    _patch_response(QUOTA_URL, status=500)
    assert_that(VeraRandom).raises(HTTPError)


@mark.parametrize('mock_response, output', [('12345\n67890\n11111', 0.12345_67890_11111),
                                            ('457\n98765\n4', 0.00457_98765_00004)])
@responses.activate
def test_random(patch_vera_quota: VeraFactory, mock_response: str, output: float):
    assert_rand_call_output(patch_vera_quota(), 'random',
                            mock_response=mock_response, output=output)


@mark.parametrize('lower, upper, mock_response, output', [(1, 20, '17', 17)])
@responses.activate
def test_single_randint(patch_vera_quota: VeraFactory, lower: int, upper: int, mock_response: str,
                        output: int):
    assert_rand_call_output(patch_vera_quota(), 'randint', lower, upper,
                            mock_response=mock_response, output=output)


@mark.parametrize('lower, upper, n, mock_response, output',
                  [(1, 3, 5, '3\n3\n1\n2\n1', [3, 3, 1, 2, 1])])
@responses.activate
def test_randints(patch_vera_quota: VeraFactory, lower: int, upper: int, n: int, mock_response: str,
                  output: List[int]):
    assert_rand_call_output(patch_vera_quota(), 'randint', lower, upper, n,
                            mock_response=mock_response, output=output)


@responses.activate
def test_max_number_of_integers(patch_vera_quota: VeraRandom):
    patch_vera_quota().check_rand_parameters(1, 5, MAX_NUMBER_OF_INTEGERS)


@responses.activate
def test_too_many_integers(patch_vera_quota: VeraRandom):
    assert_that(patch_vera_quota().check_rand_parameters).raises(TooManyRandomNumbersRequested).\
        when_called_with(1, 5, MAX_NUMBER_OF_INTEGERS + 1)


@responses.activate
def test_max_integer(patch_vera_quota: VeraRandom):
    patch_vera_quota().check_rand_parameters(1, MAX_INTEGER, 1)


@responses.activate
def test_integer_too_large(patch_vera_quota: VeraRandom):
    assert_that(patch_vera_quota().check_rand_parameters).raises(RandomNumberTooLarge).\
        when_called_with(1, MAX_INTEGER + 1, 1)


@responses.activate
def test_min_integer(patch_vera_quota: VeraRandom):
    patch_vera_quota().check_rand_parameters(1, MIN_INTEGER, 1)


@responses.activate
def test_integer_too_small(patch_vera_quota: VeraRandom):
    assert_that(patch_vera_quota().check_rand_parameters).raises(RandomNumberTooSmall).\
        when_called_with(MIN_INTEGER - 1, 1, 1)


def assert_rand_call_output(vera: VeraRandom, method: str, *args, mock_response: str, output: Any):
    _patch_int_response(mock_response)

    with mock.patch.object(vera, 'check_quota') as check_quota, \
            mock.patch.object(vera, 'check_rand_parameters') as check_rand_parameters:
        assert_that(getattr(vera, method)(*args)).is_equal_to(output)

        check_quota.assert_called_once()
        check_rand_parameters.assert_called_once()
