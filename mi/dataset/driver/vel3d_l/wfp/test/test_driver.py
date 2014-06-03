"""
@package mi.dataset.driver.vel3d_l.wfp.test.test_driver
@file marine-integrations/mi/dataset/driver/vel3d_l/wfp/driver.py
@author Steve Myerson (Raytheon)
@brief Test cases for vel3d_l_wfp driver (for both telemetered and recovered data)

USAGE:
 Make tests verbose and provide stdout
   * From the IDK
       $ bin/dsa/test_driver
       $ bin/dsa/test_driver -i [-t testname]
       $ bin/dsa/test_driver -q [-t testname]
"""

__author__ = 'Steve Myerson (Raytheon)'
__license__ = 'Apache 2.0'

import unittest

from nose.plugins.attrib import attr
from mock import Mock

from mi.core.log import get_logger; log = get_logger()
import os

from mi.core.exceptions import \
    DatasetParserException, \
    RecoverableSampleException, \
    SampleException, \
    UnexpectedDataException

from mi.idk.dataset.unit_test import DataSetTestCase
from mi.idk.dataset.unit_test import DataSetIntegrationTestCase
from mi.idk.dataset.unit_test import DataSetQualificationTestCase
from mi.idk.exceptions import IDKConfigMissing, IDKException, SampleTimeout
from mi.idk.util import remove_all_files

from mi.dataset.dataset_driver import \
    DataSourceConfigKey, \
    DataSetDriverConfigKeys, \
    DriverParameter

from pyon.agent.agent import ResourceAgentState
from interface.objects import ResourceAgentErrorEvent

from mi.dataset.driver.vel3d_l.wfp.driver import \
    Vel3dLWfp, \
    DataTypeKey

from mi.dataset.parser.sio_mule_common import StateKey
from mi.dataset.parser.vel3d_l_wfp import \
    Vel3dLWfpDataParticleType, \
    Vel3dLWfpStateKey, \
    Vel3dLWfpInstrumentParticle, \
    Vel3dLWfpMetadataParticle, \
    Vel3dLWfpSioMuleMetadataParticle

DIR_REC = '/tmp/dsatest_rec'
DIR_TEL = '/tmp/dsatest_tel'
FILE_REC1 = 'A00000001.DAT'
FILE_REC2 = 'A00000002.DAT'
FILE_REC4 = 'A00000004.DAT'
FILE_TEL = 'node58p1.dat'

# Fill in driver details
DataSetTestCase.initialize(
    driver_module='mi.dataset.driver.vel3d_l.wfp.driver',
    driver_class='Vel3dLWfp',
    agent_resource_id = '123xyz',
    agent_name = 'Agent007',
    agent_packet_config = Vel3dLWfp.stream_config(),
    startup_config = {
        DataSourceConfigKey.RESOURCE_ID: 'vel3d_l_wfp',
        DataSourceConfigKey.HARVESTER:
        {
            DataTypeKey.VEL3D_L_WFP:
            {
                DataSetDriverConfigKeys.DIRECTORY: DIR_REC,
                DataSetDriverConfigKeys.PATTERN: 'A*.DAT',
                DataSetDriverConfigKeys.FREQUENCY: 1,
            },
            DataTypeKey.VEL3D_L_WFP_SIO_MULE:
            {
                DataSetDriverConfigKeys.DIRECTORY: DIR_TEL,
                DataSetDriverConfigKeys.PATTERN: FILE_TEL,
                DataSetDriverConfigKeys.FREQUENCY: 1,
            }
        },
        DataSourceConfigKey.PARSER: {}
    }
)

PARSER_STATE = 'parser_state'

REC_PARTICLES = (Vel3dLWfpInstrumentParticle, Vel3dLWfpMetadataParticle)
TEL_PARTICLES = (Vel3dLWfpInstrumentParticle, Vel3dLWfpSioMuleMetadataParticle)

# The integration and qualification tests generated here are suggested tests,
# but may not be enough to fully test your driver. Additional tests should be
# written as needed.

###############################################################################
#                            INTEGRATION TESTS                                #
# Device specific integration tests are for                                   #
# testing device specific capabilities                                        #
###############################################################################
@attr('INT', group='mi')
class IntegrationTest(DataSetIntegrationTestCase):

    def test_get(self):
        """
        Test that we can get data from multiple files.
        """
        log.info("================ START INTEG TEST GET =====================")

        # Start sampling.
        self.clear_sample_data()
        self.driver.start_sampling()

        # Generated recovered file has 10 instrument
        # records and 1 metadata record.
        log.info("FILE rec_vel3d_l_1.dat INTEG TEST GET")
        self.clear_async_data()
        self.create_sample_data_set_dir('rec_vel3d_l_1.dat', DIR_REC, FILE_REC1)
        self.assert_data(REC_PARTICLES, 'rec_vel3d_l_1.yml', count=11, timeout=11)

        # Generated telemetered file has 1 SIO block with 10 instrument
        # records and 1 metadata record.
        log.info("FILE tel_vel3d_l_1.dat INTEG TEST GET")
        self.clear_async_data()
        self.create_sample_data_set_dir('tel_vel3d_l_1.dat', DIR_TEL, FILE_TEL)
        self.assert_data(TEL_PARTICLES, 'tel_vel3d_l_1.yml', count=11, timeout=11)

        log.info("================ END INTEG TEST GET ======================")

    def test_get_any_order(self):
        """
        Test that we can get data from files for all harvesters / parsers.
        This isn't a good test since both parsers generate INSTRUMENT particle streams.
        So all files processed by 1 harvester need to be handled before files
        by the other harvester, or the INSTRUMENT particles will get interspersed.
        """
        log.info("=========== START INTEG TEST GET ANY ORDER  ================")

        # Start sampling.
        self.clear_sample_data()
        self.driver.start_sampling()
        self.clear_async_data()

        # Set up the test files.
        # 2 Recovered files
        #   rec_vel3d_l_2 - 4 instrument, 1 metadata, 6 instrument, 1 metadata
        #   rec_vel3d_l_4 - 1 instrument, 2 instrument, 3 instrument,
        #                   4 instrument with metadata after each group
        # 1 Telemetered file
        #   tel_vel3d_l_1 - 10 instrument, 1 metadata
        log.info("=========== CREATE DATA FILES  ================")
        self.create_sample_data_set_dir('rec_vel3d_l_4.dat', DIR_REC, FILE_REC4)
        self.create_sample_data_set_dir('rec_vel3d_l_2.dat', DIR_REC, FILE_REC2)

        # Read files in the following order:
        # Entire recovered data file rec_vel3d_l_2.
        # Entire recovered data file rec_vel3d_l_4.
        # Entire telemetered data file tel_vel3d_l_1.
        log.info("=========== READ RECOVERED DATA FILE #1  ================")
        self.assert_data(REC_PARTICLES, 'rec_vel3d_l_2.yml', count=12, timeout=12)

        log.info("=========== READ RECOVERED DATA FILE #2  ================")
        self.assert_data(REC_PARTICLES, 'rec_vel3d_l_4.yml', count=14, timeout=14)

        log.info("=========== READ TELEMETERED DATA FILE #1  ================")
        self.create_sample_data_set_dir('tel_vel3d_l_1.dat', DIR_TEL, FILE_TEL)
        self.assert_data(TEL_PARTICLES, 'tel_vel3d_l_1.yml', count=11, timeout=11)

        log.info("=========== END INTEG TEST GET ANY ORDER  ================")

    def test_non_vel3d_l_sio_block(self):
        """
        Test ability of the parser to ignore SIO blocks which are not vel3d_l blocks.
        """
        log.info("=========== START INTEG NON VEL3D_L SIO BLOCK  ================")

        # Generated telemetered file has 3 SIO blocks.
        # First SIO block is not a VEL3D_L SIO Block.
        # Second SIO block has 3 instrument records and 1 metadata record.
        # Third SIO block has 4 instrument records and 1 metadata record.
        log.info("FILE tel_vel3d_l_3.dat INTEG TEST GET")
        self.clear_async_data()
        self.create_sample_data_set_dir('tel_vel3d_l_3.dat', DIR_TEL, FILE_TEL)
        self.driver.start_sampling()
        self.assert_data(TEL_PARTICLES, 'tel_vel3d_l_3.yml', count=9, timeout=9)

        log.info("=========== END INTEG NON VEL3D_L SIO BLOCK  ================")

    def test_stop_resume(self):
        """
        Test the ability to stop and restart the process
        """
        log.info("=========== START INTEG TEST STOP RESUME  ================")

        self.clear_async_data()
        path_1 = self.create_sample_data_set_dir('rec_vel3d_l_1.dat', DIR_REC, FILE_REC1)
        path_2 = self.create_sample_data_set_dir('rec_vel3d_l_4.dat', DIR_REC, FILE_REC4)

        # Recovered file 1 position set to EOF.
        # Recovered file 2 position set to record 9 (start of group of 4 records).
        pos_1 = 761
        pos_2 = 1155    # 338 + 385 + 432

        key_rec = DataTypeKey.VEL3D_L_WFP
        key_tel = DataTypeKey.VEL3D_L_WFP_SIO_MULE

        state = {
            key_rec:
                {FILE_REC1: self.get_file_state(path_1, True, pos_1),
                 FILE_REC4: self.get_file_state(path_2, False, pos_2)},
            key_tel:
                {}
        }

        log.info("===== INTEG TEST STOP RESUME SET STATE TO %s =======", state)
        self.driver = self._get_driver_object(memento=state)
        self.driver.start_sampling()

        log.info("=========== READ RECOVERED DATA FILE #2  ================")
        self.assert_data(REC_PARTICLES, 'rec_vel3d_l_4_10-14.yml', count=5, timeout=10)

        log.info("=========== END INTEG TEST STOP RESUME  ================")

    def test_stop_start_resume(self):
        """
        Test the ability to stop and restart sampling, ingesting files in the
        correct order
        """
        log.info("========== START INTEG TEST STOP START RESUME  ===============")
        self.clear_async_data()

        self.create_sample_data_set_dir('rec_vel3d_l_1.dat', DIR_REC, FILE_REC1)
        self.create_sample_data_set_dir('rec_vel3d_l_2.dat', DIR_REC, FILE_REC2)

        self.driver.start_sampling()

        # Read all the records from rec_vel3d_l_1.dat.
        log.info("=========== READ RECOVERED DATA FILE #1  ================")
        self.assert_data(REC_PARTICLES, 'rec_vel3d_l_1.yml', count=11, timeout=11)
        self.assert_file_ingested(FILE_REC1, DataTypeKey.VEL3D_L_WFP)

        # Read 5 records (of 12) from rec_vel3d_l_2.dat.
        log.info("=========== READ RECOVERED DATA FILE #2  ================")
        self.assert_data(REC_PARTICLES, 'rec_vel3d_l_2_1-5.yml', count=5, timeout=5)

        # Stop and then start sampling, resuming from where we left off.
        self.driver.stop_sampling()
        self.driver.start_sampling()

        # Read the last 7 records (of 12) from rec_vel3d_l_2.dat.
        log.info("=========== READ RECOVERED DATA FILE #2  ================")
        self.assert_data(REC_PARTICLES, 'rec_vel3d_l_2_6-12.yml', count=7, timeout=7)
        self.assert_file_ingested(FILE_REC2, DataTypeKey.VEL3D_L_WFP)

        log.info("=========== END INTEG TEST STOP START RESUME  ================")

    def test_sample_exception(self):
        """
        Test a case that should produce a sample exception and confirm the
        sample exception occurs
        """
        log.info("======== START INTEG TEST SAMPLE EXCEPTION FAMILY ==========")

        self.clear_sample_data()
        self.clear_async_data()
        self.create_sample_data_set_dir('rec_excess.dat', DIR_REC, FILE_REC1)
        self.driver.start_sampling()

        # an event catches the sample exception - excess data at end of record
        self.assert_event('ResourceAgentErrorEvent')

        log.info("======== END INTEG TEST SAMPLE EXCEPTION FAMILY ==========")

###############################################################################
#                            QUALIFICATION TESTS                              #
# Device specific qualification tests are for                                 #
# testing device specific capabilities                                        #
###############################################################################
@attr('QUAL', group='mi')
class QualificationTest(DataSetQualificationTestCase):

    def test_parser_exception(self):
        """
        Test an exception is raised after the driver is started during
        record parsing.
        """
        log.info("========== START QUAL TEST PARSER EXCEPTION ==========")

        self.clear_sample_data()
        self.event_subscribers.clear_events()
        self.assert_initialize()
        self.create_sample_data_set_dir('rec_excess.dat', DIR_REC, FILE_REC1)

        # Verify an event was raised and we are in our retry state.
        self.assert_event_received(ResourceAgentErrorEvent, 10)
        self.assert_state_change(ResourceAgentState.STREAMING, 10)

        log.info("========== END QUAL TEST PARSER EXCEPTION ==========")

    def test_publish_path(self):
        """
        Setup an agent/driver/harvester/parser and verify that data is
        published out the agent
        """
        log.info("=========== START QUAL TEST PUBLISH PATH =================")

        # Generated telemetered file has 1 SIO block with 10 instrument
        # records and 1 metadata record.
        log.info("FILE tel_vel3d_l_1.dat QUAL TEST PUBLISH PATH")
        self.create_sample_data_set_dir('tel_vel3d_l_1.dat', DIR_TEL, FILE_TEL)
        self.assert_initialize(final_state=ResourceAgentState.COMMAND)
        self.assert_start_sampling()

        try:
            # Verify that we get 10 instrument particles from the telemetered data file.
            samples = 10
            particle = Vel3dLWfpDataParticleType.INSTRUMENT_PARTICLE
            log.info("===== READ %d TELEMETERED INSTRUMENT PARTICLES =====", samples)
            result = self.data_subscribers.get_samples(particle, samples, 30)

            # Verify that we get 1 metadata particle from the telemetered data file.
            samples = 1
            particle = Vel3dLWfpDataParticleType.SIO_METADATA_PARTICLE
            log.info("===== READ %d TELEMETERED METADATA PARTICLES =====", samples)
            meta_result = self.data_subscribers.get_samples(particle, samples, 10)

            # Combine the instrument and metadata particles and verify results.
            result.extend(meta_result)
            self.assert_data_values(result, 'tel_vel3d_l_1.yml')

        except Exception as e:
            log.error("Telemetered Exception trapped: %s", e)
            self.fail("Sample timeout.")

        self.assert_stop_sampling()

        # Generated recovered file has 10 instrument records and 1 metadata record.
        log.info("FILE rec_vel3d_l_1.dat QUAL TEST PUBLISH PATH")
        self.create_sample_data_set_dir('rec_vel3d_l_1.dat', DIR_REC, FILE_REC1)
        self.assert_start_sampling()

        try:
            # Verify that we get 10 instrument particles from the recovered data file.
            samples = 10
            particle = Vel3dLWfpDataParticleType.INSTRUMENT_PARTICLE
            log.info("===== READ %d RECOVERED INSTRUMENT PARTICLES =====", samples)
            result = self.data_subscribers.get_samples(particle, samples, 30)

            # Verify that we get 1 metadata particle from the recovered data file.
            samples = 1
            particle = Vel3dLWfpDataParticleType.WFP_METADATA_PARTICLE
            log.info("===== READ %d RECOVERED METADATA PARTICLES =====", samples)
            meta_result = self.data_subscribers.get_samples(particle, samples, 10)

            # Combine the instrument and metadata particles and verify results.
            result.extend(meta_result)
            self.assert_data_values(result, 'rec_vel3d_l_1.yml')

        except Exception as e:
            log.error("Recovered Exception trapped: %s", e)
            self.fail("Sample timeout.")

        log.info("=========== END QUAL TEST PUBLISH PATH =================")

    def test_rec_large_import(self):
        """
        Test importing a large number of samples at once from the recovered file
        """
        log.info("========= START QUAL TEST RECOVERED LARGE IMPORT ============")

        # The recovered data file referenced in the IDD contains 1 data record
        # which contains 14124 instrument records and 1 metadata record.
        self.create_sample_data_set_dir('A0000001.DAT', DIR_REC, 'A0000001.DAT')

        self.assert_initialize(final_state=ResourceAgentState.COMMAND)
        self.assert_start_sampling()

        log.info("========== READING RECOVERED PARTICLES ==============")
        try:
            samples = 14124
            particle = Vel3dLWfpDataParticleType.INSTRUMENT_PARTICLE
            log.info("===== READ %d RECOVERED INSTRUMENT PARTICLES =====", samples)
            self.data_subscribers.get_samples(particle, samples, 1000)

            samples = 1
            particle = Vel3dLWfpDataParticleType.WFP_METADATA_PARTICLE
            log.info("===== READ %d RECOVERED METADATA PARTICLES =====", samples)
            self.data_subscribers.get_samples(particle, samples, 5)

        except SampleTimeout as e:
            log.error("Exception trapped: %s", e, exc_info=True)
            self.fail("Sample timeout.")

        log.info("========= END QUAL TEST RECOVERED LARGE IMPORT =============")

    def test_shutdown_restart(self):
        """
        Test a full stop of the dataset agent, then restart the agent
        and confirm it restarts at the correct spot.
        """
        log.info("========== START QUAL TEST SHUTDOWN RESTART ===============")

        # This file has 2 sets of telemetered data.
        # First set has 4 instrument records and second set has 6.
        # 1 metadata record for each set.
        self.create_sample_data_set_dir('tel_vel3d_l_2.dat', DIR_TEL, FILE_TEL)
        inst_particle = Vel3dLWfpDataParticleType.INSTRUMENT_PARTICLE
        meta_particle = Vel3dLWfpDataParticleType.SIO_METADATA_PARTICLE

        self.assert_initialize(final_state=ResourceAgentState.COMMAND)
        log.info("========== START TELEMETERED SAMPLING  ===============")
        self.assert_start_sampling()

        try:
            # Verify that we get 4 instrument particles from the telemetered data file.
            samples = 4
            log.info("===== READ %d TELEMETERED INSTRUMENT PARTICLES =====", samples)
            result = self.data_subscribers.get_samples(inst_particle, samples, 10)

            # Verify that we get 1 metadata particle from the telemetered data file.
            samples = 1
            log.info("===== READ %d TELEMETERED METADATA PARTICLES =====", samples)
            meta_result = self.data_subscribers.get_samples(meta_particle, samples, 10)

            # Combine the instrument and metadata particles and verify results.
            result.extend(meta_result)
            self.assert_data_values(result, 'tel_vel3d_l_2_1-5.yml')
            log.info("========== STOP TELEMETERED SAMPLING AND AGENT ===============")
            self.assert_stop_sampling()

            # Stop the agent
            self.stop_dataset_agent_client()
            # Re-start the agent
            self.init_dataset_agent_client()
            # Re-initialize
            self.assert_initialize(final_state=ResourceAgentState.COMMAND)

            # Restart sampling and get the last 6 instrument particles of
            # telemetered file and combine with the previous ones we read.
            log.info("========== RESTART TELEMETERED ===============")
            self.assert_start_sampling()
            samples = 6
            log.info("===== READ %d TELEMETERED INSTRUMENT PARTICLES (RESTART) =====",
                     samples)
            inst_result = self.data_subscribers.get_samples(inst_particle, samples, 10)
            result.extend(inst_result)

            # Verify that we get 1 metadata particle from the telemetered data file.
            samples = 1
            log.info("===== READ %d TELEMETERED METADATA PARTICLES (RESTART) =====",
                     samples)
            meta_result = self.data_subscribers.get_samples(meta_particle, samples, 10)

            # Combine the instrument and metadata particles and verify results.
            result.extend(meta_result)
            self.assert_data_values(result, 'tel_vel3d_l_2.yml')

        except SampleTimeout as e:
            log.error("Telemetered Exception trapped: %s", e, exc_info=True)
            self.fail("Telemetered Sample timeout.")

        self.assert_stop_sampling()

        # This file has 2 sets of recovered data.
        # First set has 4 instrument records and second set has 6.
        # 1 metadata record for each set.
        self.create_sample_data_set_dir('rec_vel3d_l_2.dat', DIR_REC, FILE_REC2)
        meta_particle = Vel3dLWfpDataParticleType.WFP_METADATA_PARTICLE
        log.info("========== START RECOVERED SAMPLING  ===============")
        self.assert_start_sampling()

        try:
            # Verify that we get 4 instrument particles from the recovered data file.
            samples = 4
            log.info("===== READ %d RECOVERED INSTRUMENT PARTICLES =====", samples)
            result = self.data_subscribers.get_samples(inst_particle, samples, 10)

            # Verify that we get 1 metadata particle from the recovered data file.
            samples = 1
            log.info("===== READ %d RECOVERED METADATA PARTICLES =====", samples)
            meta_result = self.data_subscribers.get_samples(meta_particle, samples, 10)

            # Combine the instrument and metadata particles and verify results.
            result.extend(meta_result)
            self.assert_data_values(result, 'rec_vel3d_l_2_1-5.yml')
            log.info("========== STOP RECOVERED SAMPLING AND AGENT ===============")
            self.assert_stop_sampling()

            # Stop the agent
            self.stop_dataset_agent_client()
            # Re-start the agent
            self.init_dataset_agent_client()
            # Re-initialize
            self.assert_initialize(final_state=ResourceAgentState.COMMAND)

            # Restart sampling and get the last 6 instrument particles of recovered
            # file and combine with the previous ones we read.
            log.info("========== RESTART RECOVERED ===============")
            self.assert_start_sampling()
            samples = 6
            log.info("===== READ %d RECOVERED INSTRUMENT PARTICLES (RESTART) =====",
                     samples)
            inst_result = self.data_subscribers.get_samples(inst_particle, samples, 10)
            result.extend(inst_result)

            # Verify that we get 1 metadata particle from the recovered data file.
            samples = 1
            log.info("===== READ %d RECOVERED METADATA PARTICLES (RESTART) =====",
                     samples)
            meta_result = self.data_subscribers.get_samples(meta_particle, samples, 10)

            # Combine the instrument and metadata particles and verify results.
            result.extend(meta_result)
            self.assert_data_values(result, 'rec_vel3d_l_2.yml')

        except SampleTimeout as e:
            log.error("Recovered Exception trapped: %s", e, exc_info=True)
            self.fail("Recovered Sample timeout.")

        log.info("========== END QUAL TEST SHUTDOWN RESTART ===============")

    def test_stop_start(self):
        """
        Test the agents ability to start data flowing, stop, then restart
        at the correct spot.
        """
        log.info("========== START QUAL TEST STOP START ===============")

        # This file has 2 sets of recovered data.
        # First set has 4 instrument records and second set has 6.
        # 1 metadata record for each set.
        self.create_sample_data_set_dir('rec_vel3d_l_2.dat', DIR_REC, FILE_REC2)
        inst_particle = Vel3dLWfpDataParticleType.INSTRUMENT_PARTICLE
        meta_particle = Vel3dLWfpDataParticleType.WFP_METADATA_PARTICLE

        self.assert_initialize(final_state=ResourceAgentState.COMMAND)
        log.info("========== START RECOVERED SAMPLING  ===============")
        self.assert_start_sampling()

        try:
            # Verify that we get 4 instrument particles from the recovered data file.
            samples = 4
            log.info("===== READ %d RECOVERED INSTRUMENT PARTICLES =====", samples)
            result = self.data_subscribers.get_samples(inst_particle, samples, 10)

            # Verify that we get 1 metadata particle from the recovered data file.
            samples = 1
            log.info("===== READ %d RECOVERED METADATA PARTICLES =====", samples)
            meta_result = self.data_subscribers.get_samples(meta_particle, samples, 10)

            # Combine the instrument and metadata particles and verify results.
            result.extend(meta_result)
            self.assert_data_values(result, 'rec_vel3d_l_2_1-5.yml')
            log.info("========== STOP RECOVERED SAMPLING  ===============")
            self.assert_stop_sampling()

            # Restart sampling and get the last 6 instrument particles of recovered
            # file and combine with the previous ones we read.
            log.info("========== RESTART RECOVERED ===============")
            self.assert_start_sampling()
            samples = 6
            log.info("===== READ %d RECOVERED INSTRUMENT PARTICLES (RESTART) =====",
                     samples)
            inst_result = self.data_subscribers.get_samples(inst_particle, samples, 10)
            result.extend(inst_result)

            # Verify that we get 1 metadata particle from the recovered data file.
            samples = 1
            log.info("===== READ %d RECOVERED METADATA PARTICLES (RESTART) =====",
                     samples)
            meta_result = self.data_subscribers.get_samples(meta_particle, samples, 10)

            # Combine the instrument and metadata particles and verify results.
            result.extend(meta_result)
            self.assert_data_values(result, 'rec_vel3d_l_2.yml')

        except SampleTimeout as e:
            log.error("Recovered Exception trapped: %s", e, exc_info=True)
            self.fail("Recovered Sample timeout.")

        log.info("========== STOP SAMPLING  ===============")
        self.assert_stop_sampling()

        # Now repeat for an SIO file with similar contents.
        # This file has 2 sets of telemetered data.
        # First set has 4 instrument records and second set has 6.
        # 1 metadata record for each set.
        self.create_sample_data_set_dir('tel_vel3d_l_2.dat', DIR_TEL, FILE_TEL)
        meta_particle = Vel3dLWfpDataParticleType.SIO_METADATA_PARTICLE
        log.info("========== START TELEMETERED SAMPLING  ===============")
        self.assert_start_sampling()

        try:
            # Verify that we get 4 instrument particles from the telemetered data file.
            samples = 4
            log.info("===== READ %d TELEMETERED INSTRUMENT PARTICLES =====", samples)
            result = self.data_subscribers.get_samples(inst_particle, samples, 10)

            # Verify that we get 1 metadata particle from the telemetered data file.
            samples = 1
            log.info("===== READ %d TELEMETERED METADATA PARTICLES =====", samples)
            meta_result = self.data_subscribers.get_samples(meta_particle, samples, 10)

            # Combine the instrument and metadata particles and verify results.
            result.extend(meta_result)
            self.assert_data_values(result, 'tel_vel3d_l_2_1-5.yml')
            log.info("========== STOP TELEMETERED SAMPLING  ===============")
            self.assert_stop_sampling()

            # Restart sampling and get the last 6 instrument particles of
            # telemetered file and combine with the previous ones we read.
            log.info("========== RESTART TELEMETERED ===============")
            self.assert_start_sampling()
            samples = 6
            log.info("===== READ %d TELEMETERED INSTRUMENT PARTICLES (RESTART) =====",
                     samples)
            inst_result = self.data_subscribers.get_samples(inst_particle, samples, 10)
            result.extend(inst_result)

            # Verify that we get 1 metadata particle from the telemetered data file.
            samples = 1
            log.info("===== READ %d TELEMETERED METADATA PARTICLES (RESTART) =====",
                     samples)
            meta_result = self.data_subscribers.get_samples(meta_particle, samples, 10)

            # Combine the instrument and metadata particles and verify results.
            result.extend(meta_result)
            self.assert_data_values(result, 'tel_vel3d_l_2.yml')

        except SampleTimeout as e:
            log.error("Telemetered Exception trapped: %s", e, exc_info=True)
            self.fail("Telemetered Sample timeout.")

        log.info("========== END QUAL TEST STOP START ===============")

    def test_tel_large_import(self):
        """
        Test importing a large number of samples at once from the telemetered file
        """
        log.info("======= START QUAL TEST TELEMETERED LARGE IMPORT =============")

        # The telemetered data file referenced in the IDD contains 454 vel3d_l SIO
        # blocks which contain 16374 instrument records and 1 metadata record for
        # each SIO block.
        self.create_sample_data_set_dir('node58p1.dat', DIR_TEL, FILE_TEL)

        self.assert_initialize(final_state=ResourceAgentState.COMMAND)
        self.assert_start_sampling()

        log.info("========== READING TELEMETERED PARTICLES ==============")
        try:
            samples = 16374
            particle = Vel3dLWfpDataParticleType.INSTRUMENT_PARTICLE
            log.info("===== READ %d TELEMETERED INSTRUMENT PARTICLES =====", samples)
            self.data_subscribers.get_samples(particle, samples, 1000)

            samples = 454
            particle = Vel3dLWfpDataParticleType.SIO_METADATA_PARTICLE
            log.info("===== READ %d TELEMETERED METADATA PARTICLES =====", samples)
            self.data_subscribers.get_samples(particle, samples, 300)

        except SampleTimeout as e:
            log.error("Exception trapped: %s", e, exc_info=True)
            self.fail("Sample timeout.")

        log.info("========= END QUAL TEST TELEMETERED LARGE IMPORT =============")

