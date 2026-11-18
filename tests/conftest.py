"""
Global test isolation for the B3 test suite.

Several parser classes monkeypatch class level state when instantiated (the
UrT42/43 parsers replace ``b3.clients.Clients.newClient`` in ``__new__``).
Without a reset, every test module that runs later in the same process (or
xdist worker) inherits that patch and creates clients through the wrong
factory. Restore the pristine method before and after every test.

Tests that need the patched factory construct their parser in ``setUp``, which
re-applies the patch.
"""

import unittest

import pytest

from b3.clients import Clients

_PRISTINE_NEW_CLIENT = Clients.newClient


if not hasattr(unittest.TestCase, "assertDictContainsSubset"):
    # the stdlib removed it in python 3.12; the suite still uses it in 92 places
    def _assert_dict_contains_subset(self, subset, dictionary, msg=None):
        """Check that every key/value of `subset` is present in `dictionary`."""
        self.assertEqual(dict(subset.items()),
                         {k: v for k, v in dictionary.items() if k in subset},
                         msg)

    unittest.TestCase.assertDictContainsSubset = _assert_dict_contains_subset


@pytest.fixture(autouse=True)
def _pristine_client_factory():
    Clients.newClient = _PRISTINE_NEW_CLIENT
    yield
    Clients.newClient = _PRISTINE_NEW_CLIENT
