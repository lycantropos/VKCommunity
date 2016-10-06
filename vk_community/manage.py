import unittest

import click

from vk_community.tests.test_data_access import UnitTestDataAccess, UnitTestDataAccessExceptions


@click.group(name='test', invoke_without_command=False)
def test():
    pass


@test.command(name='test_dao')
def test_data_access():
    """Tests implemented data access"""
    suite = unittest.TestLoader().loadTestsFromTestCase(UnitTestDataAccess)
    unittest.TextTestRunner(verbosity=2).run(suite)
    exc_suite = unittest.TestLoader().loadTestsFromTestCase(UnitTestDataAccessExceptions)
    unittest.TextTestRunner(verbosity=2).run(exc_suite)


if __name__ == '__main__':
    test()
