from __future__ import print_function
"""
    * Starts some servers (identified uniquely by name) asynchronously
      on the local machine;
    * Each server adds the address/port information to the given file;
    * Check if all servers are ready by checking above files;
    * Abort if any servers fail to generate above files in time;
    * Update test suite with above information;
    * Run the auto-reconnect tests using touchstone monitor

    * on abort, core/mini-dump files are saved on ./test_output
    * procdump is supported on Windows
"""

__all__ = ['Execute', 'Debug']

import os
from collections import namedtuple

import ata.log
from Booster.Remove import removeSingleFile
import Booster.CheckFileExists
import Booster.ReplaceInFile
import Booster.Shared.BackgroundCommands
import Booster.TouchstoneTestList

_logger = ata.log.AtaLog(__name__)
_is_win = os.name == 'nt'

ServerDescription = namedtuple('ServerDescription', ['name', 'path', 'parameters', 'launchOptions'])
RunningServer = namedtuple('RunningServer', ['name', 'address', 'port'])


def Execute(root):
    _execute(root, False)


def Debug(root):
    _execute(root, True)


def _checked_get(node, key, parent_tag):
    """ guarantee to get attribute key
    """
    # note: parent_tag is not required, which is used for diagnosis,
    # and always
    #   node.tag == parent_tag
    val = node.attrib.get(key)
    if val is None:
        raise RuntimeError("'{0}' attribute must be provided on {1} node!".format(key, parent_tag))
        
    return val


def _checked_find(node, tag, parent_tag):
    """ guarantee to get child node tag
    """
    # note: parent_tag is not required, which is used for diagnosis,
    # and always
    #   node.tag == parent_tag
    result = node.find(tag)
    if result is None:
        raise RuntimeError("'{0}' node must be provided under {1} node!".format(tag, parent_tag))
        
    return result


def _execute(root, debug):
    print('==============================')
    print('        Enter AutoReconnectTest')
    print('==============================')

    # how it works
    #
    # test inputs are defined by attributes
    #   TestEnv
    #   TestSuite
    #   Prefix              output prefix
    #   Touchstone          full-path of touchstone binary
    #   cwd                 touchstone working directory
    #   timeout             connection timeout (sec)
    #   DMEncoding          DM encoding
    #
    # prelaunch one or more servers (<Servers>) asynchrously
    #   each server creates a file {name}_ListenAddresses.txt when ready
    # wait and check above files
    #   if not, kill all servers and abort
    # run test-list
    # kill all servers
    # 
    # if a server is killed or abort, gz dump is saved at core_folder,
    # which is ./test_output by default, overwritten by LaunchOptions.core_folder

    servers = _get_servers(root)
    timeout = root.attrib.get('Timeout', 60)
    env_file = _checked_get(root, 'TestEnv', 'AutoReconnectTest')
    suite_file = _checked_get(root, 'TestSuite', 'AutoReconnectTest')
    output_prefix  = _checked_get(root, 'Prefix', 'AutoReconnectTest')
    touchstone_binary = _checked_get(root, 'Touchstone', 'AutoReconnectTest')
    cwd = _checked_get(root, 'cwd', 'AutoReconnectTest')
    dm_encoding = root.attrib.get("DMEncoding")
    
    _logger.info('timeout={0}'.format(timeout))
    _logger.info('env_file={0}'.format(env_file))
    _logger.info('suite_file={0}'.format(suite_file))
    _logger.info('output_prefix={0}'.format(output_prefix))
    _logger.info('touchstone_binary={0}'.format(touchstone_binary))
    _logger.info('cwd={0}'.format(cwd))
    _logger.info('dm_encoding={0}'.format(dm_encoding))
    _logger.info('servers')
    for s in servers:
        _logger.info('    name={0} {1} {2}'.format(
            s.name, s.path, ' '.join(s.parameters)))
    if debug:
        return
    
    started_servers = []
    kwarg = {
        'sig': 'SIGABRT',
        'timeout': 5
    }
    try:
        started_servers += _start_servers(servers)
        running_servers = _get_running_servers(started_servers, timeout)
        _update_suite_file(suite_file, running_servers)
        outdir = os.path.join(cwd, 'test_output')
        if not Booster.TouchstoneTestList.RunOneTestSuite(env_file,
                                                          suite_file,
                                                          output_prefix,
                                                          touchstone_binary,
                                                          cwd=cwd,
                                                          outdir=outdir,
                                                          dm_encoding=dm_encoding):
            raise RuntimeError("Could not find testsuite '{0}'!".format(suite_file))
        del kwarg['sig']      # let it terminate gracefully, do not create core
        Booster.TouchstoneTestList.CopyTouchstoneOutputToDestination(outdir)
    finally:
        _stop_servers(started_servers, **kwarg)


def _get_servers(root):
    """ return list of servers by parsing xml node
    
    each server is a named-tuple

        name          unique server name
        path          full-path of server binary
        parameters    list of command-line parameters
        LaunchOptions dictionary of launch options, e.g. procdump, core_folder

        path + parameters will be passed to subprocess as command

    """
    result = []
    names = set()
    delay = 0
    delay_between = 1
    for server in _checked_find(root, 'Servers', 'AutoReconnectTest'):
        name = server.tag
        if name in names:
            raise RuntimeError("Servers must have unique names ('{0}' duplicated)".format(name))
        path = _checked_get(server, 'Path', 'Server')
        parameters = ['-ReportListenAddresses', _get_listen_address_file_name(name)]
        params_node = server.find('Parameters')
        if params_node is not None:
            for param_node in params_node:
                parameters.append('-' + param_node.tag)
                if param_node.text is not None:
                    parameters.append(param_node.text)

        # launch options with default values, customized by <LaunchOptions>
        launch_option = {
            'core_folder': os.path.abspath('test_output'),
            'stdout': '{0}_stdout.log'.format(name),

        }

        launch_options_node = server.find('LaunchOptions')
        if launch_options_node is not None:
            # see details in Booster.Shared.BackgroundCommands
            for option in launch_options_node:
                launch_option[option.tag] = option.text

        if _is_win and 'procdump' not in launch_option:
            # by default we enable procdump and try to find it
            try:
                # first try convention
                procdump = Booster.Shared.BackgroundCommands.get_executable_bin(r'c:\opt\procdump\procdump.exe')
            except ValueError as e:
                # then try to search PATH
                procdump = Booster.Shared.BackgroundCommands.get_executable_bin('procdump.exe')
            launch_option['procdump'] = procdump

        # add delay between servers, support customized delay in the mean time
        if 'delay-to-launch' not in launch_option:
            if delay > 0:
                launch_option['delay-to-launch'] = delay
        else:
            try:
                last_delay = int(launch_option['delay-to-launch'])
                if last_delay > delay:
                    delay = last_delay
            except:
                pass
        delay += delay_between

        result.append(ServerDescription(name, path, parameters, launch_option))
        names.add(name)
    return result


def _start_servers(servers):
    """ start processes that are defined in list servers, and return a list of started servers
    """
    started_servers = []
    for s in servers:
        removeSingleFile(_get_listen_address_file_name(s.name))
        Booster.Shared.BackgroundCommands.start(s.name,
            [s.path] + s.parameters,
            **s.launchOptions)
        started_servers.append(s.name)
    return started_servers


def _get_running_servers(started_servers, timeout):
    """ return a list of servers information of given server list before timeout
        
        Server information is loaded from file ({name}_ListenAddresses.txt)
        that is created by the server as the mark that the server is ready.
        
        if any files are missing before timeout, an exception is thrown
    
    param:  started_servers         a list of process names
    param:  timeout                 value in seconds
    return: list of tuple           (name, address, port)
    """
    result = []

    files = [_get_listen_address_file_name(name) for name in started_servers]
    Booster.CheckFileExists.Run(files, timeout=timeout)
    
    for name, path in zip(started_servers, files):
        with open(path) as f:
            first_line = f.readline()
            components = first_line.split()
            address = components[0]
            port = components[1]
            
            result.append(RunningServer(name, address, port))
            
    return result


def _update_suite_file(suite_file, running_servers):
    """ update test suites, with actual values (e.g. address, port)
        from files running_servers
    """
    def create_server_xml(server):
        import xml.etree.ElementTree as ET
        
        root = ET.Element(server.name)
        listening_on = ET.SubElement(root, 'ListeningOn')
        listening_on.set("ID", "1")
        address = ET.SubElement(listening_on, 'Address')
        address.text = server.address
        port = ET.SubElement(listening_on, 'Port')
        port.text = server.port
        
        return ET.tostring(root)
        
    replacement = "\n".join(create_server_xml(server) for server in running_servers)

    Booster.ReplaceInFile.replace(suite_file, '<AUTO_RECONNECT_SERVER_DEFINITIONS/>', replacement)


def _stop_servers(started_servers, **kwarg):
    """ stop processes that have name in start_servers, generate cores if applicable

    param: started_servers      list of names of processes
    param: kwarg                args that decide how the process terminates
    """
    for server in started_servers:
        _logger.info('stop server.{} with params {}'.format(server.name, kwarg))
        Booster.Shared.BackgroundCommands.stop(server, **kwarg)


def _get_listen_address_file_name(name):
    return os.path.abspath("{0}_ListenAddresses.txt".format(name))
