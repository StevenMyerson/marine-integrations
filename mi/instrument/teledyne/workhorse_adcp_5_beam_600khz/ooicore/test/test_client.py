#!/usr/bin/env python

"""
@file mi/instrument/teledyne/workhorse_adcp_5_beam_600khz/ooicore/test/test_client.py
@author Carlos Rueda
@brief VADCP Client tests
"""

__author__ = "Carlos Rueda"
__license__ = 'Apache 2.0'

from mi.instrument.teledyne.workhorse_adcp_5_beam_600khz.ooicore.client import VadcpClient
from mi.instrument.teledyne.workhorse_adcp_5_beam_600khz.ooicore.defs import md_section_names
from mi.instrument.teledyne.workhorse_adcp_5_beam_600khz.ooicore.pd0 import PD0DataStructure
from mi.instrument.teledyne.workhorse_adcp_5_beam_600khz.ooicore.util import prefix
from mi.instrument.teledyne.workhorse_adcp_5_beam_600khz.ooicore.receiver import \
    ReceiverBuilder

from mi.core.mi_logger import mi_logger as log

from mi.instrument.teledyne.workhorse_adcp_5_beam_600khz.ooicore.test import VadcpTestCase
from nose.plugins.attrib import attr


@attr('UNIT', group='mi')
class ClientTest(VadcpTestCase):

    # this class variable is to keep a single reference to the VadcpClient
    # object in the current test. setUp will first finalize such object in case
    # tearDown/cleanup does not get called. Note that any test with an error
    # will likely make subsequent tests immediately fail because of the
    # potential problem with a second connection.
    _client = None

    @classmethod
    def _end_client_if_any(cls):
        """Ends the current VadcpClient, if any."""
        if ClientTest._client:
            log.info("releasing not finalized VadcpClient object")
            try:
                ClientTest._client.end()
            finally:
                ClientTest._client = None

    @classmethod
    def tearDownClass(cls):
        """Make sure we end the last VadcpClient object if still remaining."""
        try:
            cls._end_client_if_any()
        finally:
            super(ClientTest, cls).tearDownClass()

    def setUp(self):
        """
        Sets up and connects the _client.
        """

        ReceiverBuilder.use_greenlets()

        ClientTest._end_client_if_any()

        super(ClientTest, self).setUp()

        self._ensembles_recd = 0
        outfile = file('vadcp_output.txt', 'w')
        prefix_state = True
        _client = VadcpClient(self._conn_config, outfile, prefix_state)

        # set the class and instance variables to refer to this object:
        ClientTest._client = self._client = _client

        # prepare client including going to the main menu
        _client.set_data_listener(self._data_listener)
        _client.set_generic_timeout(self._timeout)

        log.info("connecting")
        _client.connect()

    def tearDown(self):
        """
        Ends the _client.
        """
        ReceiverBuilder.use_default()
        client = ClientTest._client
        ClientTest._client = None
        try:
            if client:
                log.info("ending VadcpClient object")
                client.end()
        finally:
            super(ClientTest, self).tearDown()

    def _data_listener(self, pd0):
        self._ensembles_recd += 1
        log.info("_data_listener: received PD0=%s" % prefix(pd0))

    def test_connect_disconnect(self):
        state = self._client.get_current_state()
        log.info("current instrument state: %s" % str(state))

    def test_get_latest_ensemble(self):
        pd0 = self._client.get_latest_ensemble()
        self.assertTrue(pd0 is None or isinstance(pd0, PD0DataStructure))

    def test_get_metadata(self):
        sections = None  # all sections
        result = self._client.get_metadata(sections)
        self.assertTrue(isinstance(result, dict))
        s = ''
        for name, text in result.items():
            self.assertTrue(name in md_section_names)
            s += "**%s:%s\n\n" % (name, prefix(text, "\n    "))
        log.info("METADATA result=%s" % prefix(s))

    def test_execute_run_recorder_tests(self):
        result = self._client.run_recorder_tests()
        log.info("run_recorder_tests result=%s" % prefix(result))

    def test_all_tests(self):
        result = self._client.run_all_tests()
        log.info("ALL TESTS result=%s" % prefix(result))

    def test_send_break(self):
        result = self._client.send_break()
        self.assertTrue(isinstance(result, bool))
        log.info("send_break result=%s" % result)
