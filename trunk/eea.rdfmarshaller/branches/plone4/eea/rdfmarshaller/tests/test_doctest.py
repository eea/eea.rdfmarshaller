""" Doc tests
"""
import doctest
import unittest
from eea.rdfmarshaller.tests.base import FunctionalTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite


OPTIONFLAGS = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


def test_suite():
    """ Suite
    """
    return unittest.TestSuite((
            FunctionalDocFileSuite('marshall.txt',
                  optionflags=OPTIONFLAGS,
                  package='eea.rdfmarshaller',
                  test_class=FunctionalTestCase),
            FunctionalDocFileSuite('schema.txt',
                  optionflags=OPTIONFLAGS,
                  package='eea.rdfmarshaller',
                  test_class=FunctionalTestCase),
            ))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
