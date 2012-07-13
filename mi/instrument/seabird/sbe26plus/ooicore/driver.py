"""
@package mi.instrument.seabird.sbe26plus.ooicore.driver
@file /Users/unwin/OOI/Workspace/code/marine-integrations/mi/instrument/seabird/sbe26plus/ooicore/driver.py
@author Roger Unwin
@brief Driver for the ooicore
Release notes:

None.
"""

__author__ = 'Roger Unwin'
__license__ = 'Apache 2.0'

import string

import re
import time

from mi.core.common import BaseEnum
from mi.core.instrument.instrument_protocol import CommandResponseInstrumentProtocol
from mi.core.instrument.instrument_fsm import InstrumentFSM
from mi.core.instrument.instrument_driver import SingleConnectionInstrumentDriver
from mi.core.instrument.instrument_driver import DriverEvent
from mi.core.instrument.instrument_driver import DriverAsyncEvent
from mi.core.instrument.instrument_driver import DriverProtocolState
from mi.core.instrument.instrument_driver import DriverParameter

from mi.core.exceptions import InstrumentTimeoutException
from mi.core.exceptions import InstrumentParameterException
from mi.core.exceptions import SampleException
from mi.core.exceptions import InstrumentStateException
from mi.core.exceptions import InstrumentProtocolException

from mi.core.log import get_logger ; log = get_logger()


# newline.
NEWLINE = '\r\n'

# default timeout.
TIMEOUT = 40

# Packet config
#PACKET_CONFIG = {
#    'parsed' : None,
#    'raw' : None
#}

class ProtocolState(BaseEnum):
    """
    Protocol states
    enum.
    """
    UNKNOWN = DriverProtocolState.UNKNOWN
    COMMAND = DriverProtocolState.COMMAND
    AUTOSAMPLE = DriverProtocolState.AUTOSAMPLE
    TEST = DriverProtocolState.TEST
    CALIBRATE = DriverProtocolState.CALIBRATE
    DIRECT_ACCESS = DriverProtocolState.DIRECT_ACCESS

class ProtocolEvent(BaseEnum):
    """
    Protocol events
    """
    ENTER = DriverEvent.ENTER
    EXIT = DriverEvent.EXIT
    GET = DriverEvent.GET
    SET = DriverEvent.SET
    DISCOVER = DriverEvent.DISCOVER
    ACQUIRE_SAMPLE = DriverEvent.ACQUIRE_SAMPLE
    START_AUTOSAMPLE = DriverEvent.START_AUTOSAMPLE
    STOP_AUTOSAMPLE = DriverEvent.STOP_AUTOSAMPLE
    TEST = DriverEvent.TEST
    RUN_TEST = DriverEvent.RUN_TEST
    CALIBRATE = DriverEvent.CALIBRATE
    EXECUTE_DIRECT = DriverEvent.EXECUTE_DIRECT
    START_DIRECT = DriverEvent.START_DIRECT
    STOP_DIRECT = DriverEvent.STOP_DIRECT


# Device specific parameters.
class Parameter(DriverParameter):
    """
    Device parameters
    """

    # DS
    TXREALTIME = 'TXREALTIME'
    TXWAVEBURST = 'TXWAVEBURST'
    TXWAVESTATS = 'TXWAVESTATS'
    TIDE_SAMPLES_PER_DAY = 'TIDE_SAMPLES_PER_DAY'
    WAVE_BURSTS_PER_DAY = 'WAVE_BURSTS_PER_DAY'
    MEMORY_ENDURANCE_DAYS = 'MEMORY_ENDURANCE_DAYS'
    NOMINAL_ALKALINE_BATTERY_ENDURANCE_DAYS = 'NOMINAL_ALKALINE_BATTERY_ENDURANCE_DAYS'
    TOTAL_RECORDED_TIDE_MEASUREMENTS = 'TOTAL_RECORDED_TIDE_MEASUREMENTS'
    TOTAL_RECORDED_WAVE_BURSTS = 'TOTAL_RECORDED_WAVE_BURSTS'
    TIDE_MEASUREMENTS_SINCE_LAST_START = 'TIDE_MEASUREMENTS_SINCE_LAST_START'
    WAVE_BURSTS_SINCE_LAST_START = 'WAVE_BURSTS_SINCE_LAST_START'
    TIDE_SAMPLES_BETWEEN_WAVE_MEASUREMENTS = 'TIDE_SAMPLES_BETWEEN_WAVE_MEASUREMENTS'
    LOGGING = 'LOGGING'
    STATUS = 'STATUS'
    CONDUCTIVITY = 'CONDUCTIVITY'
    USER_INFO = 'USER_INFO'
    TIDE_MEASUREMENT_INTERVAL = 'TIDE_MEASUREMENT_INTERVAL'
    TIDE_MEASUREMENT_DURATION = 'TIDE_MEASUREMENT_DURATION'
    QUARTZ_PREASURE_SENSOR_SERIAL_NUMBER = 'QUARTZ_PREASURE_SENSOR_SERIAL_NUMBER'
    QUARTZ_PREASURE_SENSOR_RANGE = 'QUARTZ_PREASURE_SENSOR_RANGE'
    WAVE_SAMPLES_PER_BURST = 'WAVE_SAMPLES_PER_BURST'
    WAVE_SAMPLES_SCANS_PER_SECOND = 'WAVE_SAMPLES_SCANS_PER_SECOND'
    WAVE_SAMPLES_DURATION_SECONDS ='WAVE_SAMPLES_DURATION_SECONDS'
    LAST_SAMPLE_P = 'LAST_SAMPLE_P'
    LAST_SAMPLE_T = 'LAST_SAMPLE_T'
    LAST_SAMPLE_S = 'LAST_SAMPLE_S'
    IOP_MA = 'IOP_MA'
    VMAIN_V = 'VMAIN_V'
    VLITH_V = 'VLITH_V'

    # DC
    PCALDATE = 'PCALDATE'
    TCALDATE = 'TCALDATE'
    CCALDATE = 'CCALDATE'
    PU0 = 'PU0'
    PY1 = 'PY1'
    PY2 = 'PY2'
    PY3 = 'PY3'
    PC1 = 'PC1'
    PC2 = 'PC2'
    PC3 = 'PC3'
    PD1 = 'PD1'
    PD2 = 'PD2'
    PT1 = 'PT1'
    PT2 = 'PT2'
    PT3 = 'PT3'
    PT4 = 'PT4'
    PA0 = 'PA0'
    PA1 = 'PA1'
    PA2 = 'PA2'
    #PTCA0 = 'PTCA0'
    #PTCA1 = 'PTCA1'
    #PTCA2 = 'PTCA2'
    PTCB0 = 'PTCB0'
    PTCB1 = 'PTCB1'
    PTCB2 = 'PTCB2'
    #PTEMPA0 = 'PTEMPA0'
    #PTEMPA1 = 'PTEMPA1'
    #PTEMPA2 = 'PTEMPA2'
    POFFSET = 'POFFSET'
    TA0 = 'TA0'
    TA1 = 'TA1'
    TA2 = 'TA2'
    TA3 = 'TA3'
    CG = 'CG'
    CH = 'CH'
    CI = 'CI'
    CJ = 'CJ'
    CTCOR = 'CTCOR'
    CPCOR = 'CPCOR'
    CSLOPE = 'CSLOPE'
    FACTORY_M = 'FACTORY_M'
    FACTORY_B = 'FACTORY_B'


# Device prompts.
class Prompt(BaseEnum):
    """
    sbe26plus io prompts.
    """
    COMMAND = 'S>'
    BAD_COMMAND = '? cmd S>'
    AUTOSAMPLE = 'S>'

"""
S>
time out

SBE 26plus
S>
"""
###############################################################################
# Driver
###############################################################################

class InstrumentDriver(SingleConnectionInstrumentDriver):
    """
    InstrumentDriver subclass
    Subclasses SingleConnectionInstrumentDriver with connection state
    machine.
    """
    def __init__(self, evt_callback):
        """
        Driver constructor.
        @param evt_callback Driver process event callback.
        """
        #Construct superclass.
        SingleConnectionInstrumentDriver.__init__(self, evt_callback)

    ########################################################################
    # Superclass overrides for resource query.
    ########################################################################

    def get_resource_params(self):
        """
        Return list of device parameters available.
        """
        return Parameter.list()

    ########################################################################
    # Protocol builder.
    ########################################################################

    def _build_protocol(self):
        """
        Construct the driver protocol state machine.
        """
        self._protocol = Protocol(Prompt, NEWLINE, self._driver_event)

###############################################################################
# Protocol
################################################################################


class Protocol(CommandResponseInstrumentProtocol):
    """
    Instrument protocol class for sbe26plus driver.
    Subclasses CommandResponseInstrumentProtocol
    """
    def __init__(self, prompts, newline, driver_event):
        """
        Protocol constructor.
        @param prompts A BaseEnum class containing instrument prompts.
        @param newline The sbe26plus newline.
        @param driver_event Driver process event callback.
        """
        # Construct protocol superclass.
        CommandResponseInstrumentProtocol.__init__(self, prompts, newline, driver_event)

        # Build sbe26plus protocol state machine.
        self._protocol_fsm = InstrumentFSM(ProtocolState, ProtocolEvent,
            ProtocolEvent.ENTER, ProtocolEvent.EXIT)

        # Add event handlers for protocol state machine.
        self._protocol_fsm.add_handler(ProtocolState.UNKNOWN, ProtocolEvent.ENTER, self._handler_unknown_enter)
        self._protocol_fsm.add_handler(ProtocolState.UNKNOWN, ProtocolEvent.EXIT, self._handler_unknown_exit)
        self._protocol_fsm.add_handler(ProtocolState.UNKNOWN, ProtocolEvent.DISCOVER, self._handler_unknown_discover)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.ENTER, self._handler_command_enter)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.EXIT, self._handler_command_exit)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.ACQUIRE_SAMPLE, self._handler_command_acquire_sample)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.START_AUTOSAMPLE, self._handler_command_start_autosample)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.GET, self._handler_command_autosample_test_get)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.SET, self._handler_command_set)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.TEST, self._handler_command_test)
        self._protocol_fsm.add_handler(ProtocolState.COMMAND, ProtocolEvent.START_DIRECT, self._handler_command_start_direct)
        self._protocol_fsm.add_handler(ProtocolState.AUTOSAMPLE, ProtocolEvent.ENTER, self._handler_autosample_enter)
        self._protocol_fsm.add_handler(ProtocolState.AUTOSAMPLE, ProtocolEvent.EXIT, self._handler_autosample_exit)
        self._protocol_fsm.add_handler(ProtocolState.AUTOSAMPLE, ProtocolEvent.GET, self._handler_command_autosample_test_get)
        self._protocol_fsm.add_handler(ProtocolState.AUTOSAMPLE, ProtocolEvent.STOP_AUTOSAMPLE, self._handler_autosample_stop_autosample)
        self._protocol_fsm.add_handler(ProtocolState.TEST, ProtocolEvent.ENTER, self._handler_test_enter)
        self._protocol_fsm.add_handler(ProtocolState.TEST, ProtocolEvent.EXIT, self._handler_test_exit)
        self._protocol_fsm.add_handler(ProtocolState.TEST, ProtocolEvent.RUN_TEST, self._handler_test_run_tests)
        self._protocol_fsm.add_handler(ProtocolState.TEST, ProtocolEvent.GET, self._handler_command_autosample_test_get)
        self._protocol_fsm.add_handler(ProtocolState.DIRECT_ACCESS, ProtocolEvent.ENTER, self._handler_direct_access_enter)
        self._protocol_fsm.add_handler(ProtocolState.DIRECT_ACCESS, ProtocolEvent.EXIT, self._handler_direct_access_exit)
        self._protocol_fsm.add_handler(ProtocolState.DIRECT_ACCESS, ProtocolEvent.EXECUTE_DIRECT, self._handler_direct_access_execute_direct)
        self._protocol_fsm.add_handler(ProtocolState.DIRECT_ACCESS, ProtocolEvent.STOP_DIRECT, self._handler_direct_access_stop_direct)

        # Construct the parameter dictionary containing device parameters,
        # current parameter values, and set formatting functions.
        self._build_param_dict()

        # Add build handlers for device commands.
        self._add_build_handler('ds', self._build_simple_command)
        self._add_build_handler('dc', self._build_simple_command)
        self._add_build_handler('ts', self._build_simple_command)
        self._add_build_handler('start', self._build_simple_command)
        self._add_build_handler('stop', self._build_simple_command)
        self._add_build_handler('tc', self._build_simple_command)
        self._add_build_handler('tt', self._build_simple_command)
        self._add_build_handler('tp', self._build_simple_command)
        self._add_build_handler('set', self._build_set_command)

        # Add response handlers for device commands.
        self._add_response_handler('ds', self._parse_dsdc_response)
        self._add_response_handler('dc', self._parse_dsdc_response)
        self._add_response_handler('ts', self._parse_ts_response)
        self._add_response_handler('set', self._parse_set_response)
        self._add_response_handler('tc', self._parse_test_response)
        self._add_response_handler('tt', self._parse_test_response)
        self._add_response_handler('tp', self._parse_test_response)

        # Add sample handlers.
        self._sample_pattern = r'^#? *(-?\d+\.\d+), *(-?\d+\.\d+), *(-?\d+\.\d+)'
        self._sample_pattern += r'(, *(-?\d+\.\d+))?(, *(-?\d+\.\d+))?'
        self._sample_pattern += r'(, *(\d+) +([a-zA-Z]+) +(\d+), *(\d+):(\d+):(\d+))?'
        self._sample_pattern += r'(, *(\d+)-(\d+)-(\d+), *(\d+):(\d+):(\d+))?'
        self._sample_regex = re.compile(self._sample_pattern)

        # State state machine in UNKNOWN state.
        self._protocol_fsm.start(ProtocolState.UNKNOWN)

        # commands sent sent to device to be filtered in responses for telnet DA
        self._sent_cmds = []



    ########################################################################
    # Unknown handlers.
    ########################################################################

    def _handler_unknown_enter(self, *args, **kwargs):
        """
        Enter unknown state.
        """
        # Tell driver superclass to send a state change event.
        # Superclass will query the state.
        self._driver_event(DriverAsyncEvent.STATE_CHANGE)

    def _handler_unknown_exit(self, *args, **kwargs):
        """
        Exit unknown state.
        """
        pass

    def _handler_unknown_discover(self, *args, **kwargs):
        """
        Discover current state; can be COMMAND or AUTOSAMPLE.
        @retval (next_state, result), (ProtocolState.COMMAND or
        State.AUTOSAMPLE, None) if successful.
        @throws InstrumentTimeoutException if the device cannot be woken.
        @throws InstrumentStateException if the device response does not correspond to
        an expected state.
        """
        next_state = None
        result = None

        # Wakeup the device with timeout if passed.
        timeout = kwargs.get('timeout', TIMEOUT)
        prompt = self._wakeup(timeout)
        prompt = self._wakeup(timeout)

        # Set the state to change.
        # Raise if the prompt returned does not match command or autosample.
        if prompt == Prompt.COMMAND:
            next_state = ProtocolState.COMMAND
            result = ProtocolState.COMMAND
        elif prompt == Prompt.AUTOSAMPLE:
            next_state = ProtocolState.AUTOSAMPLE
            result = ProtocolState.AUTOSAMPLE
        else:
            raise InstrumentStateException('Unknown state.')

        return (next_state, result)

    ########################################################################
    # Command handlers.
    ########################################################################

    def _handler_command_enter(self, *args, **kwargs):
        """
        Enter command state.
        @throws InstrumentTimeoutException if the device cannot be woken.
        @throws InstrumentProtocolException if the update commands and not recognized.
        """
        # Command device to update parameters and send a config change event.
        self._update_params()

        # Tell driver superclass to send a state change event.
        # Superclass will query the state.
        self._driver_event(DriverAsyncEvent.STATE_CHANGE)

    def _handler_command_exit(self, *args, **kwargs):
        """
        Exit command state.
        """
        pass

    def _handler_command_set(self, *args, **kwargs):
        """
        Perform a set command.
        @param args[0] parameter : value dict.
        @retval (next_state, result) tuple, (None, None).
        @throws InstrumentParameterException if missing set parameters, if set parameters not ALL and
        not a dict, or if paramter can't be properly formatted.
        @throws InstrumentTimeoutException if device cannot be woken for set command.
        @throws InstrumentProtocolException if set command could not be built or misunderstood.
        """
        next_state = None
        result = None

        # Retrieve required parameter.
        # Raise if no parameter provided, or not a dict.
        try:
            params = args[0]

        except IndexError:
            raise InstrumentParameterException('Set command requires a parameter dict.')

        if not isinstance(params, dict):
            raise InstrumentParameterException('Set parameters not a dict.')

        # For each key, val in the dict, issue set command to device.
        # Raise if the command not understood.
        else:

            for (key, val) in params.iteritems():
                result = self._do_cmd_resp('set', key, val, **kwargs)
            self._update_params()

        return (next_state, result)

    def _handler_command_acquire_sample(self, *args, **kwargs):
        """
        Acquire sample from SBE26 Plus.
        @retval (next_state, result) tuple, (None, sample dict).
        @throws InstrumentTimeoutException if device cannot be woken for command.
        @throws InstrumentProtocolException if command could not be built or misunderstood.
        @throws SampleException if a sample could not be extracted from result.
        """
        next_state = None
        result = None

        result = self._do_cmd_resp('ts', *args, **kwargs)

        return (next_state, result)

    def _handler_command_start_autosample(self, *args, **kwargs):
        """
        Switch into autosample mode.
        @retval (next_state, result) tuple, (ProtocolState.AUTOSAMPLE,
        None) if successful.
        @throws InstrumentTimeoutException if device cannot be woken for command.
        @throws InstrumentProtocolException if command could not be built or misunderstood.
        """
        next_state = None
        result = None

        # Assure the device is transmitting.
        if not self._param_dict.get(Parameter.TXREALTIME):
            self._do_cmd_resp('set', Parameter.TXREALTIME, True, **kwargs)

        # Issue start command and switch to autosample if successful.
        self._do_cmd_no_resp('start', *args, **kwargs)

        next_state = ProtocolState.AUTOSAMPLE

        return (next_state, result)

    def _handler_command_test(self, *args, **kwargs):
        """
        Switch to test state to perform instrument tests.
        @retval (next_state, result) tuple, (ProtocolState.TEST, None).
        """
        next_state = None
        result = None

        next_state = ProtocolState.TEST

        return (next_state, result)

    def _handler_command_start_direct(self):
        """
        """
        next_state = None
        result = None

        next_state = ProtocolState.DIRECT_ACCESS

        return (next_state, result)

    ########################################################################
    # Autosample handlers.
    ########################################################################

    def _handler_autosample_enter(self, *args, **kwargs):
        """
        Enter autosample state.
        """
        # Tell driver superclass to send a state change event.
        # Superclass will query the state.
        self._driver_event(DriverAsyncEvent.STATE_CHANGE)

    def _handler_autosample_exit(self, *args, **kwargs):
        """
        Exit autosample state.
        """
        pass

    def _handler_autosample_stop_autosample(self, *args, **kwargs):
        """
        Stop autosample and switch back to command mode.
        @retval (next_state, result) tuple, (ProtocolState.COMMAND,
        None) if successful.
        @throws InstrumentTimeoutException if device cannot be woken for command.
        @throws InstrumentProtocolException if command misunderstood or
        incorrect prompt received.
        """
        next_state = None
        result = None

        # Wake up the device, continuing until autosample prompt seen.
        timeout = kwargs.get('timeout', TIMEOUT)
        self._wakeup_until(timeout, Prompt.AUTOSAMPLE)

        # Issue the stop command.
        self._do_cmd_resp('stop', *args, **kwargs)

        # Prompt device until command prompt is seen.
        self._wakeup_until(timeout, Prompt.COMMAND)

        next_state = ProtocolState.COMMAND

        return (next_state, result)

    ########################################################################
    # Common handlers.
    ########################################################################

    def _handler_command_autosample_test_get(self, *args, **kwargs):
        """
        Get device parameters from the parameter dict.
        @param args[0] list of parameters to retrieve, or DriverParameter.ALL.
        @throws InstrumentParameterException if missing or invalid parameter.
        """
        next_state = None
        result = None

        # Retrieve the required parameter, raise if not present.
        try:
            params = args[0]

        except IndexError:
            raise InstrumentParameterException('Get command requires a parameter list or tuple.')

        # If all params requested, retrieve config.
        if params == DriverParameter.ALL:
            result = self._param_dict.get_config()

        # If not all params, confirm a list or tuple of params to retrieve.
        # Raise if not a list or tuple.
        # Retireve each key in the list, raise if any are invalid.
        else:
            if not isinstance(params, (list, tuple)):
                raise InstrumentParameterException('Get argument not a list or tuple.')
            result = {}
            for key in params:
                try:
                    val = self._param_dict.get(key)
                    result[key] = val

                except KeyError:
                    raise InstrumentParameterException(('%s is not a valid parameter.' % key))

        return (next_state, result)

    ########################################################################
    # Test handlers.
    ########################################################################

    def _handler_test_enter(self, *args, **kwargs):
        """
        Enter test state. Setup the secondary call to run the tests.
        """
        # Tell driver superclass to send a state change event.
        # Superclass will query the state.
        self._driver_event(DriverAsyncEvent.STATE_CHANGE)

        # Forward the test event again to run the test handler and
        # switch back to command mode afterward.
        Timer(1, lambda: self._protocol_fsm.on_event(ProtocolEvent.RUN_TEST)).start()

    def _handler_test_exit(self, *args, **kwargs):
        """
        Exit test state.
        """
        pass

    def _handler_test_run_tests(self, *args, **kwargs):
        """
        Run test routines and validate results.
        @throws InstrumentTimeoutException if device cannot be woken for command.
        @throws InstrumentProtocolException if command misunderstood or
        incorrect prompt received.
        """
        next_state = None
        result = None

        tc_pass = False
        tt_pass = False
        tp_pass = False
        tc_result = None
        tt_result = None
        tp_result = None

        test_result = {}

        try:
            tc_pass, tc_result = self._do_cmd_resp('tc', timeout=200)
            tt_pass, tt_result = self._do_cmd_resp('tt', timeout=200)
            tp_pass, tp_result = self._do_cmd_resp('tp', timeout=200)

        except Exception as e:
            test_result['exception'] = e
            test_result['message'] = 'Error running instrument tests.'

        finally:
            test_result['cond_test'] = 'Passed' if tc_pass else 'Failed'
            test_result['cond_data'] = tc_result
            test_result['temp_test'] = 'Passed' if tt_pass else 'Failed'
            test_result['temp_data'] = tt_result
            test_result['pres_test'] = 'Passed' if tp_pass else 'Failed'
            test_result['pres_data'] = tp_result
            test_result['success'] = 'Passed' if (tc_pass and tt_pass and tp_pass) else 'Failed'

        self._driver_event(DriverAsyncEvent.TEST_RESULT, test_result)
        next_state = ProtocolState.COMMAND

        return (next_state, result)

    ########################################################################
    # Direct access handlers.
    ########################################################################

    def _handler_direct_access_enter(self, *args, **kwargs):
        """
        Enter direct access state.
        """
        # Tell driver superclass to send a state change event.
        # Superclass will query the state.
        self._driver_event(DriverAsyncEvent.STATE_CHANGE)

        self._sent_cmds = []

    def _handler_direct_access_exit(self, *args, **kwargs):
        """
        Exit direct access state.
        """
        pass

    def _handler_direct_access_execute_direct(self, data):
        """
        """
        next_state = None
        result = None

        self._do_cmd_direct(data)

        # add sent command to list for 'echo' filtering in callback
        self._sent_cmds.append(data)

        return (next_state, result)

    def _handler_direct_access_stop_direct(self):
        """
        @throw InstrumentProtocolException on invalid command
        """
        next_state = None
        result = None

        next_state = ProtocolState.COMMAND

        return (next_state, result)

    ########################################################################
    # Private helpers.
    ########################################################################

    def _send_wakeup(self):
        """
        Send a newline to attempt to wake the sbe26plus device.
        """
        self._connection.send(NEWLINE)

    def _update_params(self, *args, **kwargs):
        """
        Update the parameter dictionary. Wake the device then issue
        display status and display calibration commands. The parameter
        dict will match line output and udpate itself.
        @throws InstrumentTimeoutException if device cannot be timely woken.
        @throws InstrumentProtocolException if ds/dc misunderstood.
        """


        # Get old param dict config.
        old_config = self._param_dict.get_config()

        # Issue display commands and parse results.
        timeout = kwargs.get('timeout', TIMEOUT)
        self._do_cmd_resp('ds',timeout=timeout)
        self._do_cmd_resp('dc',timeout=timeout)

        # Get new param dict config. If it differs from the old config,
        # tell driver superclass to publish a config change event.
        new_config = self._param_dict.get_config()
        if new_config != old_config:
            self._driver_event(DriverAsyncEvent.CONFIG_CHANGE)

    def _build_simple_command(self, cmd):
        """
        Build handler for basic sbe26plus commands.
        @param cmd the simple sbe37 command to format.
        @retval The command to be sent to the device.
        """
        return cmd + NEWLINE

    def _build_set_command(self, cmd, param, val):
        """
        Build handler for set commands. param=val followed by newline.
        String val constructed by param dict formatting function.
        @param param the parameter key to set.
        @param val the parameter value to set.
        @ retval The set command to be sent to the device.
        @throws InstrumentProtocolException if the parameter is not valid or
        if the formatting function could not accept the value passed.
        """
        try:
            str_val = self._param_dict.format(param, val)
            set_cmd = '%s=%s' % (param, str_val)
            set_cmd = set_cmd + NEWLINE

        except KeyError:
            raise InstrumentParameterException('Unknown driver parameter %s' % param)

        return set_cmd

    def _parse_set_response(self, response, prompt):
        """
        Parse handler for set command.
        @param response command response string.
        @param prompt prompt following command response.
        @throws InstrumentProtocolException if set command misunderstood.
        """
        log.debug("PROMPT = " + str(prompt))
        if prompt != Prompt.COMMAND:
            raise InstrumentProtocolException('Set command not recognized: %s' % response)

    def _parse_dsdc_response(self, response, prompt):
        """
        Parse handler for dsdc commands.
        @param response command response string.
        @param prompt prompt following command response.
        @throws InstrumentProtocolException if dsdc command misunderstood.
        """
        log.debug("in _parse_dsdc_response")

        if prompt != Prompt.COMMAND:
            raise InstrumentProtocolException('dsdc command not recognized: %s.' % response)
            #
        # Need to tweek the input to contain one param per line.
        #
        """
        SBE 26plus V 6.1e  SN 1328    11 Jul 2012  14:32:20
        quartz pressure sensor: serial number = 123404, range = 100 psia
        iop =  6.1 ma  vmain = 17.4 V  vlith =  9.0 V
        last sample: p = -99.0000, t = -99.0000, s = -99.0000
        tide measurement: interval = 10.000 minutes, duration = 30 seconds
        4 wave samples/burst at 4.00 scans/sec, duration = 1 seconds
        logging start time =  10 Jul 2012  17:38:10
        logging stop time =  01 Jan 2100  01:01:01
        """

        modified_response = ""
        for line in response.split(NEWLINE):
            line = re.sub("SBE 26plus V ([0-9a-zA-Z\.]+) +SN (\d+) +(\d+ [a-zA-Z]{3} \d{4})  (\d+:\d\d:\d\d)",
                "SBE 26plus V - VERSION \\1" + NEWLINE +
                "SBE 26plus V - SERIAL NUMBER \\2" + NEWLINE +
                "SBE 26plus V - SERIAL NUMBER DATE \\3" + NEWLINE +
                "SBE 26plus V - SERIAL NUMBER TIME \\4" + NEWLINE, line)
            # line = re.sub(" find ", " replacement ", line)

            modified_response = modified_response + line

        log.debug("************ DS/DC OUTPUT => '" + str(line) + "'")

        for line in modified_response.split(NEWLINE):
            name = self._param_dict.update(line)



    def _parse_ts_response(self, response, prompt):
        """
        Response handler for ts command.
        @param response command response string.
        @param prompt prompt following command response.
        @retval sample dictionary containig c, t, d values.
        @throws InstrumentProtocolException if ts command misunderstood.
        @throws InstrumentSampleException if response did not contain a sample
        """
        log.debug("************ in _parse_ts_response ")
        """
        S>ts
        ts
           14.6343  22.99  22.7395 -1.02527   0.0000
        (pressure psia, pressure temperature C, temperature C, conductivity S/m, and salinity psu)
        """

        log.debug("PROMPT = " + str(prompt) + " WANTED " + str(Prompt.COMMAND))
        if prompt != Prompt.COMMAND:
            raise InstrumentProtocolException('ts command not recognized: %s', response)


        sample = None
        for line in response.split(NEWLINE):
            sample = self._extract_sample(line, True)
            if sample:
                break

        if not sample:
            raise SampleException('Response did not contain sample: %s' % repr(response))

        return sample

    def _parse_test_response(self, response, prompt):
        """
        Do minimal checking of test outputs.
        @param response command response string.
        @param promnpt prompt following command response.
        @retval tuple of pass/fail boolean followed by response
        """
        log.debug("************ in _parse_test_response ")
        success = False
        lines = response.split()
        if len(lines)>2:
            data = lines[1:-1]
            bad_count = 0
            for item in data:
                try:
                    float(item)

                except ValueError:
                    bad_count += 1

            if bad_count == 0:
                success = True

        return (success, response)

    def got_data(self, data):
        """
        Callback for receiving new data from the device.
        """

        if self.get_current_state() == ProtocolState.DIRECT_ACCESS:
            # direct access mode
            if len(data) > 0:
                #mi_logger.debug("Protocol._got_data(): <" + data + ">")
                # check for echoed commands from instrument (TODO: this should only be done for telnet?)
                if len(self._sent_cmds) > 0:
                    # there are sent commands that need to have there echoes filtered out
                    oldest_sent_cmd = self._sent_cmds[0]
                    if string.count(data, oldest_sent_cmd) > 0:
                        # found a command echo, so remove it from data and delete the command form list
                        data = string.replace(data, oldest_sent_cmd, "", 1)
                        self._sent_cmds.pop(0)
                if len(data) > 0 and self._driver_event:
                    self._driver_event(DriverAsyncEvent.DIRECT_ACCESS, data)
                    # TODO: what about logging this as an event?
            return

        if len(data)>0:
            # Call the superclass to update line and prompt buffers.
            CommandResponseInstrumentProtocol.got_data(self, data)

            # If in streaming mode, process the buffer for samples to publish.
            cur_state = self.get_current_state()
            if cur_state == ProtocolState.AUTOSAMPLE:
                if NEWLINE in self._linebuf:
                    lines = self._linebuf.split(NEWLINE)
                    self._linebuf = lines[-1]
                    for line in lines:
                        self._extract_sample(line)

    def _extract_sample(self, line, publish=True):
        """
        Extract sample from a response line if present and publish to agent.
        @param line string to match for sample.
        @param publsih boolean to publish sample (default True).
        @retval Sample dictionary if present or None.
        """



        """
        tide: start time = 11 Jul 2012 12:53:51, p = 14.6398, pt = 23.321, t = 23.0060, c = -1.02527, s = 0.0000
        tide: start time = 11 Jul 2012 13:01:45, p = 14.6384, pt = 23.251, t = 22.9377, c = -1.02527, s = 0.0000
        """
        log.debug("************ in _extract_sample GOT LINE => " + repr(line))
        sample = None
        match = self._sample_regex.match(line)
        if match:
            sample = {}
            sample['t'] = [float(match.group(1))]
            sample['c'] = [float(match.group(2))]
            sample['p'] = [float(match.group(3))]

            # Driver timestamp.
            sample['time'] = [time.time()]
            sample['stream_name'] = 'ctd_parsed'

            if self._driver_event:
                self._driver_event(DriverAsyncEvent.SAMPLE, sample)

        return sample

    def _build_param_dict(self):
        """
        Populate the parameter dictionary with sbe26plus parameters.
        For each parameter key, add match stirng, match lambda function,
        and value formatting function for set commands.

        """
        # Add parameter handlers to parameter dict.
        log.debug("************ in _build_param_dict ")


        """
        SBE 26plus V 6.1e  SN 1328    10 Jul 2012  13:50:15
        *DONE*user info=whoi
        *DONE*quartz pressure sensor: serial number = 123404, range = 100 psia
        internal temperature sensor
        *DONE*conductivity = YES
        *DONE*iop =  6.1 ma  vmain = 17.4 V  vlith =  9.0 V
        *DONE*last sample: p = 14.5064, t = 23.1834, s = -99.0000

        *DONE*tide measurement: interval = 10.000 minutes, duration = 60 seconds
        *DONE*measure waves every 2 tide samples
        *DONE*512 wave samples/burst at 1.00 scans/sec, duration = 512 seconds

        (A)
        logging start time = do not use start time
        logging stop time = do not use stop time
        -------------------------------------------
        (B)
        logging start time =  01 Jan 2100  01:01:01
        logging stop time =  01 Jan 2100  01:01:01

        *DONE*tide samples/day = 144.000
        *DONE*wave bursts/day = 72.000
        *DONE*memory endurance = 289.8 days
        *DONE*nominal alkaline battery endurance = 145.2 days
        *DONE*total recorded tide measurements = 0
        *DONE*total recorded wave bursts = 0
        *DONE*tide measurements since last start = 0
        *DONE*wave bursts since last start = 0

        *DONE*transmit real-time tide data = YES
        *DONE*transmit real-time wave burst data = YES
        *DONE*transmit real-time wave statistics = NO

        (A)
        *DONE*status = stopped by user
        *DONE*logging = NO, send start command to begin logging
        -------------------------------------------
        (B)
        *DONE*status = waiting to start at  01 Jan 2100  01:01:01
        *DONE*logging = NO, send start command to begin logging
        -------------------------------------------
        (C)
        *DONE*status = logging started
        *DONE*logging = YES


        """
        # DS
        self._param_dict.add(Parameter.TXREALTIME,
            r'transmit real-time tide data = (YES|NO)',
            lambda match : False if (match.group(1)=='NO') else True,
            self._true_false_to_string)

        self._param_dict.add(Parameter.TXWAVEBURST,
            r'transmit real-time wave burst data = (YES|NO)',
            lambda match : False if (match.group(1)=='NO') else True,
            self._true_false_to_string)

        self._param_dict.add(Parameter.TXWAVESTATS,
            r'transmit real-time wave statistics = (YES|NO)',
            lambda match : False if (match.group(1)=='NO') else True,
            self._true_false_to_string)

        self._param_dict.add(Parameter.TIDE_SAMPLES_PER_DAY,
            r'tide samples/day = (\d+.\d+)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.WAVE_BURSTS_PER_DAY,
            r'wave bursts/day = (\d+.\d+)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.MEMORY_ENDURANCE_DAYS,
            r'memory endurance = (\d+.\d+) days',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.NOMINAL_ALKALINE_BATTERY_ENDURANCE_DAYS,
            r'nominal alkaline battery endurance = (\d+.\d+) days',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.TOTAL_RECORDED_TIDE_MEASUREMENTS,
            r'total recorded tide measurements = ([\d.\-]+)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.TOTAL_RECORDED_WAVE_BURSTS,
            r'total recorded wave bursts = ([\d.\-]+)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.TIDE_MEASUREMENTS_SINCE_LAST_START,
            r'tide measurements since last start = ([\d.\-]+)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.WAVE_BURSTS_SINCE_LAST_START,
            r'wave bursts since last start = ([\d.\-]+)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.TIDE_SAMPLES_BETWEEN_WAVE_MEASUREMENTS,
            r'measure waves every ([\d.\-]+) tide samples',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.LOGGING,
            r'logging = (YES|NO)',
            lambda match : False if (match.group(1)=='NO') else True,
            self._true_false_to_string)

        self._param_dict.add(Parameter.STATUS,
            r'status = (logging|waiting|stopped)',
            lambda match : string.upper(match.group(1)),
            True) # True because if it matches, then its a string, else, it wont match

        self._param_dict.add(Parameter.CONDUCTIVITY,
            r'logging = (YES|NO)',
            lambda match : False if (match.group(1)=='NO') else True,
            self._true_false_to_string)

        self._param_dict.add(Parameter.USER_INFO,
            r'user info=(.*)$',
            lambda match : string.upper(match.group(1)),
            True) # True because if it matches, then its a string, else, it wont match

        self._param_dict.add(Parameter.TIDE_MEASUREMENT_INTERVAL,
            r'tide measurement: interval = ([\d.\-]+) minutes',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.TIDE_MEASUREMENT_DURATION,
            r'tide measurement: interval = [\d.\-]+ minutes, duration = ([\d.\-]+) seconds',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.QUARTZ_PREASURE_SENSOR_SERIAL_NUMBER,
            r'quartz pressure sensor: serial number = ([\d.\-]+), range = [\d.\-]+ psia',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.QUARTZ_PREASURE_SENSOR_RANGE,
            r'quartz pressure sensor: serial number = [\d.\-]+, range = ([\d.\-]+) psia',
            lambda match : float(match.group(1)),
            self._float_to_string)
        #4 wave samples/burst at 4.00 scans/sec, duration = 1 seconds
        # at [\d.\-]+ scans\/sec, duration = [\d.\-]+ seconds
        self._param_dict.add(Parameter.WAVE_SAMPLES_PER_BURST,
            r'(\d+) wave samples/burst at ',
            lambda match : int(match.group(1)),
            self._int_to_string)
        """
        self._param_dict.add(Parameter.WAVE_SAMPLES_SCANS_PER_SECOND,
            r'([\d.\-]+) scans/sec',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.WAVE_SAMPLES_DURATION_SECONDS,
            r'[\d.\-]+ wave samples/burst at [\d.\-]+ scans/sec, duration = ([\d.\-]+) seconds',
            lambda match : float(match.group(1)),
            self._float_to_string)
        """
        self._param_dict.add(Parameter.LAST_SAMPLE_P,
            r'last sample: p = ([\d.\-]+), t = [\d.\-]+, s = [\d.\-]+',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.LAST_SAMPLE_T,
            r'last sample: p = [\d.\-]+, t = ([\d.\-]+), s = [\d.\-]+',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.LAST_SAMPLE_S,
            r'last sample: p = [\d.\-]+, t = [\d.\-]+, s = ([\d.\-]+)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.IOP_MA,
            r'iop =  ([\d.\-]+) ma  vmain = [\d.\-]+ V  vlith =  [\d.\-]+ V',
            lambda match : float(match.group(1)),
            self._float_to_string)
        self._param_dict.add(Parameter.VMAIN_V,
            r'iop =  [\d.\-]+ ma  vmain = ([\d.\-]+) V  vlith =  [\d.\-]+ V',
            lambda match : float(match.group(1)),
            self._float_to_string)
        self._param_dict.add(Parameter.VLITH_V,
            r'iop =  [\d.\-]+ ma  vmain = [\d.\-]+ V  vlith =  ([\d.\-]+) V',
            lambda match : float(match.group(1)),
            self._float_to_string)


        # DC

        self._param_dict.add(Parameter.TCALDATE,
            r'Temperature coefficients: +((\d+)-([a-zA-Z]+)-(\d+))',
            lambda match : self._string_to_date(match.group(1), '%d-%b-%y'),
            self._date_to_string)

        self._param_dict.add(Parameter.TA0,
            r' +TA0 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.TA1,
            r' +TA1 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.TA2,
            r' +TA2 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.TA3,
            r' +TA3 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CG,
            r' +G = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CH,
            r' +H = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CI,
            r' +I = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CJ,
            r' +J = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CTCOR,
            r' +CTCOR = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CPCOR,
            r' +CPCOR = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PCALDATE,
            r'Pressure coefficients: +((\d+)-([a-zA-Z]+)-(\d+))',
            lambda match : self._string_to_date(match.group(1), '%d-%b-%y'),
            self._date_to_string)

        self._param_dict.add(Parameter.PA2,
            r' +PA2 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PTCB0,
            r' +PTCSB0 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PTCB1,
            r' +PTCSB1 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PTCB2,
            r' +PTCSB2 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        #self._param_dict.add(Parameter.PTEMPA0,
        #    r' +PTEMPA0 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
        #    lambda match : float(match.group(1)),
        #    self._float_to_string)

        #self._param_dict.add(Parameter.PTEMPA1,
        #    r' +PTEMPA1 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
        #    lambda match : float(match.group(1)),
        #    self._float_to_string)

        #self._param_dict.add(Parameter.PTEMPA2,
        #    r' +PTEMPA2 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
        #    lambda match : float(match.group(1)),
        #    self._float_to_string)

        self._param_dict.add(Parameter.POFFSET,
            r' +OFFSET = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PC1,
            r' +C1 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PC2,
            r' +C2 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PC3,
            r' +C3 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PD1,
            r' +D1 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PD2,
            r' +D2 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PY1,
            r' +Y1 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PY2,
            r' +Y2 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PY3,
            r' +Y3 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PT1,
            r' +T1 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PT2,
            r' +T2 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PT3,
            r' +T3 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PT4,
            r' +T4 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.FACTORY_M,
            r' +M = (-?[\.\d]+)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.FACTORY_B,
            r' +B = (-?[\.\d]+)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CCALDATE,
            r'Conductivity coefficients: +((\d+)-([a-zA-Z]+)-(\d+))',
            lambda match : self._string_to_date(match.group(1), '%d-%b-%y'),
            self._date_to_string)

        self._param_dict.add(Parameter.CG,
            r' +CG = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CH,
            r' +CH = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CI,
            r' +CI = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CJ,
            r' +CJ = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CTCOR,
            r' +CTCOR = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CPCOR,
            r' +CPCOR = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.CSLOPE,
            r' +CSLOPE = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PA0,
            r' +PA0 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        self._param_dict.add(Parameter.PA1,
            r' +PA1 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

        #self._param_dict.add(Parameter.PTCA0,
        #    r' +PTCA0 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
        #    lambda match : float(match.group(1)),
        #    self._float_to_string)

        #self._param_dict.add(Parameter.PTCA1,
        #    r' +PTCA1 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
        #    lambda match : float(match.group(1)),
        #    self._float_to_string)

        #self._param_dict.add(Parameter.PTCA2,
        #    r' +PTCA2 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
        #    lambda match : float(match.group(1)),
        #    self._float_to_string)

        self._param_dict.add(Parameter.PU0,
            r' +U0 = (-?\d.\d\d\d\d\d\de[-+]\d\d)',
            lambda match : float(match.group(1)),
            self._float_to_string)

    ########################################################################
    # Static helpers to format set commands.
    ########################################################################

    @staticmethod
    def _true_false_to_string(v):
        """
        Write a boolean value to string formatted for sbe37 set operations.
        @param v a boolean value.
        @retval A yes/no string formatted for sbe37 set operations.
        @throws InstrumentParameterException if value not a bool.
        """
        log.debug("************ in _true_false_to_string ")
        if not isinstance(v,bool):
            raise InstrumentParameterException('Value %s is not a bool.' % str(v))
        if v:
            return 'y'
        else:
            return 'n'

    @staticmethod
    def _int_to_string(v):
        """
        Write an int value to string formatted for sbe37 set operations.
        @param v An int val.
        @retval an int string formatted for sbe37 set operations.
        @throws InstrumentParameterException if value not an int.
        """
        log.debug("************ in _int_to_string ")
        if not isinstance(v,int):
            raise InstrumentParameterException('Value %s is not an int.' % str(v))
        else:
            return '%i' % v

    @staticmethod
    def _float_to_string(v):
        """
        Write a float value to string formatted for sbe37 set operations.
        @param v A float val.
        @retval a float string formatted for sbe37 set operations.
        @throws InstrumentParameterException if value is not a float.
        """
        log.debug("************ in _float_to_string ")

        if not isinstance(v,float):
            raise InstrumentParameterException('Value %s is not a float.' % v)
        else:
            return '%e' % v

    @staticmethod
    def _date_to_string(v):
        """
        Write a date tuple to string formatted for sbe37 set operations.
        @param v a date tuple: (day,month,year).
        @retval A date string formatted for sbe37 set operations.
        @throws InstrumentParameterException if date tuple is not valid.
        """
        log.debug("************ in _date_to_string ")
        if not isinstance(v,(list,tuple)):
            raise InstrumentParameterException('Value %s is not a list, tuple.' % str(v))

        if not len(v)==3:
            raise InstrumentParameterException('Value %s is not length 3.' % str(v))

        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep',
                  'Oct','Nov','Dec']
        day = v[0]
        month = v[1]
        year = v[2]

        if len(str(year)) > 2:
            year = int(str(year)[-2:])

        if not isinstance(day,int) or day < 1 or day > 31:
            raise InstrumentParameterException('Value %s is not a day of month.' % str(day))

        if not isinstance(month,int) or month < 1 or month > 12:
            raise InstrumentParameterException('Value %s is not a month.' % str(month))

        if not isinstance(year,int) or year < 0 or year > 99:
            raise InstrumentParameterException('Value %s is not a 0-99 year.' % str(year))

        return '%02i-%s-%02i' % (day,months[month-1],year)

    @staticmethod
    def _string_to_date(datestr,fmt):
        """
        Extract a date tuple from an sbe37 date string.
        @param str a string containing date information in sbe37 format.
        @retval a date tuple.
        @throws InstrumentParameterException if datestr cannot be formatted to
        a date.
        """
        log.debug("************ in _string_to_date ")
        if not isinstance(datestr,str):
            raise InstrumentParameterException('Value %s is not a string.' % str(datestr))
        try:
            date_time = time.strptime(datestr,fmt)
            date = (date_time[2],date_time[1],date_time[0])

        except ValueError:
            raise InstrumentParameterException('Value %s could not be formatted to a date.' % str(datestr))

        return date

