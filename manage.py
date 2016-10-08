import unittest

import click

from tests.test_app import IntegrationTestsApp
from tests.test_data_access import UnitTestsDataAccess, UnitTestsExceptionsDataAccess, IntegrationTestsDataAccess


@click.group(name='test', invoke_without_command=False)
def test():
    pass


@test.command(name='test_dao')
def test_data_access():
    """Tests implemented data access"""
    suite = unittest.TestLoader().loadTestsFromTestCase(UnitTestsDataAccess)
    unittest.TextTestRunner(verbosity=2).run(suite)
    exc_suite = unittest.TestLoader().loadTestsFromTestCase(UnitTestsExceptionsDataAccess)
    unittest.TextTestRunner(verbosity=2).run(exc_suite)
    suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTestsDataAccess)
    unittest.TextTestRunner(verbosity=2).run(suite)


@test.command(name='test_app')
def test_app():
    """Tests implemented app methods"""
    suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTestsApp)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    test()
