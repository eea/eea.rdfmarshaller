""" Doc tests
"""
import os
import doctest
import unittest
from eea.rdfmarshaller.tests.base import FunctionalTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite


OPTIONFLAGS = (
               doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


def test_suite():
    """ Suite
    """
    os.environ['PLONE_CSRF_DISABLED'] = 'true'

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
