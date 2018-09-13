from typing import Callable, Any, List, Tuple, Type
from unittest import mock

import responses
from assertpy import assert_that
from pytest import mark, raises
from requests import HTTPError

from verarandom import (
    VeraRandom, QUOTA_URL, QUOTA_LIMIT, MAX_QUOTA, BitQuotaExceeded, INTEGER_URL,
    MAX_NUMBER_OF_INTEGERS, TooManyRandomNumbersRequested, MAX_INTEGER_LIMIT,
    RandomNumberLimitTooLarge, NoRandomNumbersRequested, MIN_INTEGER_LIMIT,
    RandomNumberLimitTooSmall
)


def _patch_int_response(body: str, **kwargs):
    _patch_response(INTEGER_URL, body=body, **kwargs)


def _patch_response(url: str, method: str=responses.GET, **kwargs):
    responses.add(method, url, **kwargs)


def test_max_quota():
    _check_quota_using_randint(VeraRandom(MAX_QUOTA))


def test_valid_quota():
    _check_quota_using_randint(VeraRandom(1000))


def test_quota_limit():
    _check_quota_using_randint(VeraRandom(QUOTA_LIMIT))


def test_invalid_quota_below_limit():
    with raises(BitQuotaExceeded):
        _check_quota_using_randint(VeraRandom(QUOTA_LIMIT - 1))


@responses.activate
def test_quota_property():
    assert_that(VeraRandom(500).quota_estimate).is_equal_to(500)


@responses.activate
def test_invalid_quota_response():
    _patch_response(QUOTA_URL, status=500)
    with raises(HTTPError):
        VeraRandom().randint(1, 1)


@mark.parametrize('mock_response, output', [('12345\n67890\n11111', 0.12345_67890_11111),
                                            ('457\n98765\n4', 0.00457_98765_00004)])
@responses.activate
def test_random(mock_response: str, output: float):
    assert_rand_call_output('random', mock_response=mock_response, output=output)


@mark.parametrize('lower, upper, mock_response, output', [(1, 20, '17', 17)])
@responses.activate
def test_single_randint(lower: int, upper: int, mock_response: str,
                        output: int):
    assert_rand_call_output('randint', lower, upper, mock_response=mock_response, output=output)


@mark.parametrize('lower, upper, mock_response, output', [(1, 5, '3', [3])])
@responses.activate
def test_single_randint_as_list(lower: int, upper: int,
                                mock_response: str, output: int):
    assert_rand_call_output('randint', lower, upper, 1, mock_response=mock_response, output=output)


@mark.parametrize('lower, upper, n, mock_response, output',
                  [(1, 3, 5, '3\n3\n1\n2\n1', [3, 3, 1, 2, 1])])
@responses.activate
def test_randints(lower: int, upper: int, n: int, mock_response: str,
                  output: List[int]):
    assert_rand_call_output('randint', lower, upper, n, mock_response=mock_response, output=output)


def test_max_number_of_integers():
    _check_randint_parameters(VeraRandom(MAX_QUOTA), 1, 5, MAX_NUMBER_OF_INTEGERS)


def test_too_many_integers():
    _assert_randint_exception(VeraRandom(MAX_QUOTA), TooManyRandomNumbersRequested, 1, 5,
                              MAX_NUMBER_OF_INTEGERS + 1)


def test_min_number_of_integers():
    _check_randint_parameters(VeraRandom(MAX_QUOTA), 1, 5, 1)


def test_too_few_integers():
    _assert_randint_exception(VeraRandom(MAX_QUOTA), NoRandomNumbersRequested, 1, 5, 0)


def test_max_integer_upper_limit():
    _check_randint_parameters(VeraRandom(MAX_QUOTA), 1, MAX_INTEGER_LIMIT, 1)


def test_max_integer_too_large():
    _assert_randint_exception(VeraRandom(MAX_QUOTA), RandomNumberLimitTooLarge, 1,
                              MAX_INTEGER_LIMIT + 1, 1)


def test_max_integer_lower_limit():
    _check_randint_parameters(VeraRandom(MAX_QUOTA), 1, MIN_INTEGER_LIMIT, 1)


def test_max_integer_too_small():
    _assert_randint_exception(VeraRandom(MAX_QUOTA), RandomNumberLimitTooSmall, 1,
                              MIN_INTEGER_LIMIT - 1, 1)


def test_min_integer_upper_limit():
    _check_randint_parameters(VeraRandom(MAX_QUOTA), MAX_INTEGER_LIMIT, 1, 1)


def test_min_integer_too_large():
    _assert_randint_exception(VeraRandom(MAX_QUOTA), RandomNumberLimitTooLarge,
                              MAX_INTEGER_LIMIT + 1, 1, 1)


def test_min_integer_lower_limit():
    _check_randint_parameters(VeraRandom(), MIN_INTEGER_LIMIT, 1, 1)


def test_min_integer_too_small():
    _assert_randint_exception(VeraRandom(MAX_QUOTA), RandomNumberLimitTooSmall,
                              MIN_INTEGER_LIMIT - 1, 1, 1)


@mark.parametrize('lower, upper, n, mock_response, bits', [(1, 8, 3, '7\n1\n4', 7)])
@responses.activate
def test_quota_diminishes_after_request(lower: int, upper: int,
                                        n: int, mock_response: str, bits: int):
    _patch_int_response(mock_response)
    vera_random = VeraRandom(MAX_QUOTA)
    vera_random.randint(lower, upper, 4)
    assert_that(vera_random.quota_estimate).is_equal_to(MAX_QUOTA - bits)


@responses.activate
def _check_quota_using_randint(vera: VeraRandom):
    _patch_int_response('1')
    vera.randint(1, 1)


def assert_rand_call_output(vera_method: str, *args, mock_response: str, output: Any):
    vera = VeraRandom(MAX_QUOTA)
    _patch_int_response(mock_response)
    mock_check_quota = mock.MagicMock(side_effect=vera._request_quota_if_unset)
    _assert_patched_random_call(vera, vera_method, args, mock_check_quota, output)


def _assert_patched_random_call(vera: VeraRandom, vera_method: 'str', args: Tuple,
                                mock_check_quota: Callable, output: str):
    with mock.patch.object(vera, '_check_quota', mock_check_quota) as check_quota, \
            mock.patch.object(vera, '_check_randint_parameters') as check_parameters:
        assert_that(getattr(vera, vera_method)(*args)).is_equal_to(output)

        check_quota.assert_called_once()
        check_parameters.assert_called_once()


def _check_randint_parameters(vera: VeraRandom, *args):
    with mock.patch.object(vera, '_get_randints_from_request'):
        vera.randint(*args)


def _assert_randint_exception(vera: VeraRandom, ex: Type[Exception], *args):
    with raises(ex):
        _check_randint_parameters(vera, *args)
