from typing import Callable, Any, List, Tuple
from unittest import mock

import responses
from assertpy import assert_that
from pytest import fixture, mark
from requests import HTTPError

from verarandom import (
    VeraRandom, QUOTA_URL, QUOTA_LIMIT, MAX_QUOTA, BitQuotaExceeded, INTEGER_URL,
    MAX_NUMBER_OF_INTEGERS, TooManyRandomNumbersRequested, MAX_INTEGER_LIMIT,
    RandomNumberLimitTooLarge, NoRandomNumbersRequested, MIN_INTEGER_LIMIT,
    RandomNumberLimitTooSmall
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
def test_max_quota(patch_vera_quota: VeraFactory):
    patch_vera_quota(MAX_QUOTA).check_quota()


@responses.activate
def test_valid_quota(patch_vera_quota: VeraFactory):
    patch_vera_quota(1000).check_quota()


@responses.activate
def test_quota_limit(patch_vera_quota: VeraFactory):
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


def test_max_number_of_integers():
    VeraRandom().check_randint_request_parameters(1, 5, MAX_NUMBER_OF_INTEGERS)


def test_too_many_integers():
    assert_that(VeraRandom().check_randint_request_parameters).\
        raises(TooManyRandomNumbersRequested).when_called_with(1, 5, MAX_NUMBER_OF_INTEGERS + 1)


def test_min_number_of_integers():
    VeraRandom().check_randint_request_parameters(1, 5, 1)


def test_too_few_integers():
    assert_that(VeraRandom().check_randint_request_parameters).\
        raises(NoRandomNumbersRequested).when_called_with(1, 5, 0)


def test_max_integer_upper_limit():
    VeraRandom().check_randint_request_parameters(1, MAX_INTEGER_LIMIT, 1)


def test_max_integer_too_large():
    assert_that(VeraRandom().check_randint_request_parameters).\
        raises(RandomNumberLimitTooLarge).when_called_with(1, MAX_INTEGER_LIMIT + 1, 1)


def test_max_integer_lower_limit():
    VeraRandom().check_randint_request_parameters(1, MIN_INTEGER_LIMIT, 1)


def test_max_integer_too_small():
    assert_that(VeraRandom().check_randint_request_parameters).\
        raises(RandomNumberLimitTooSmall).when_called_with(1, MIN_INTEGER_LIMIT - 1, 1)


def test_min_integer_upper_limit():
    VeraRandom().check_randint_request_parameters(MAX_INTEGER_LIMIT, 1, 1)


def test_min_integer_too_large():
    assert_that(VeraRandom().check_randint_request_parameters).\
        raises(RandomNumberLimitTooLarge).when_called_with(MAX_INTEGER_LIMIT + 1, 1, 1)


def test_min_integer_lower_limit():
    VeraRandom().check_randint_request_parameters(MIN_INTEGER_LIMIT, 1, 1)


def test_min_integer_too_small():
    assert_that(VeraRandom().check_randint_request_parameters).\
        raises(RandomNumberLimitTooSmall).when_called_with(MIN_INTEGER_LIMIT - 1, 1, 1)


@mark.parametrize('lower, upper, n, mock_response, bits', [(1, 8, 3, '7\n1\n4', 7)])
@responses.activate
def test_quota_diminishes_after_request(patch_vera_quota: VeraRandom, lower: int, upper: int,
                                        n: int, mock_response: str, bits: int):
    _patch_int_response(mock_response)
    vera_random = patch_vera_quota()
    vera_random.randint(lower, upper, 4)
    assert_that(vera_random.remaining_quota).is_equal_to(MAX_QUOTA - bits)


def assert_rand_call_output(vera: VeraRandom, method: str, *args, mock_response: str, output: Any):
    _patch_int_response(mock_response)
    mock_check_quota = mock.MagicMock(side_effect=vera._request_quota)
    _assert_patched_random_call(vera, method, args, mock_check_quota, output)


def _assert_patched_random_call(vera: VeraRandom, method: str, args: Tuple,
                                mock_check_quota: Callable, output: str):
    with mock.patch.object(vera, 'check_quota', mock_check_quota) as check_quota, \
            mock.patch.object(vera, 'check_randint_request_parameters') as check_parameters:
        assert_that(getattr(vera, method)(*args)).is_equal_to(output)

        check_quota.assert_called_once()
        check_parameters.assert_called_once()
