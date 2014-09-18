#!/usr/bin/env python

"""
@package mi.dataset.test.test_parser Base dataset parser test code
@file mi/dataset/test/test_driver.py
@author Steve Foley
@brief Test code for the dataset parser base classes and common structures for
testing parsers.
"""
import os

from mi.core.unit_test import MiUnitTestCase, MiIntTestCase
from mi.idk.result_set import ResultSet

# Make some stubs if we need to share among parser test suites
class ParserUnitTestCase(MiUnitTestCase):
    pass

    def verify_particles(self, particles, resource_path, yml_file):
        """
        Verify that the contents of the particles match those in the result file.
        """

        rs_file = os.path.join(resource_path, yml_file)
        rs = ResultSet(rs_file)
        self.assertTrue(rs.verify(particles),
                        msg='Failed Unit test data validation')

class ParserIntTestCase(MiIntTestCase):
    pass