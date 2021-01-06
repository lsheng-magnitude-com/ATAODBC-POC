from __future__ import print_function
"""Starts some servers on the local machine, adds the address/port information to the given file, then runs the specified tests using touchstone monitor"""

__all__ = ['Execute', 'Debug']

import os
from collections import namedtuple

import ata.log
from BoosterError import BoosterError
from Remove import removeSingleFile
import BackgroundCommand
import CheckFileExists
import ReplaceInFile
import Shared.BackgroundCommands
import TouchstoneTestList
import sys
import traceback
import xml.etree.ElementTree as ET

_logger = ata.log.AtaLog(__name__)

ServerDescription = namedtuple('ServerDescription', ['name', 'path', 'parameters'])
RunningServer = namedtuple('RunningServer', ['name', 'address', 'port'])
(_commandName,_) = os.path.splitext(os.path.basename(__file__))
  
def Execute(root):
    _execute(root, False)
    
def Debug(root):
    _execute(root, True)

def _checked_get(node, key, parent_tag):
    val = node.attrib.get(key)
    if val is None:
        raise RuntimeError("'{0}' attribute must be provided on {1} node!".format(key, parent_tag))
        
    return val
    
def _checked_find(node, tag, parent_tag):
    result = node.find(tag)
    if result is None:
        raise RuntimeError("'{0}' node must be provided under {1} node!".format(tag, parent_tag))
        
    return result
    
def _getServerListValue(serverName, running_servers):
    for server in running_servers:
        if server.name == serverName:
            return server.address + ' ' + server.port
            
    raise RuntimeError("'{0}' is not a valid server name!".format(serverName))
    
def _getExtraReplacements(node, running_servers):
    topNode = node.find('ExtraReplacements')
    result = []
    if topNode is not None:
        for replacement in topNode.findall('Replacement'):
            needle = replacement.find('From').text
            to = replacement.find('To')
            
            if needle is None or to is None:
                raise RuntimeError("'{0}' is not a valid replacement!".format(ET.tostring(replacement)))
            
            if to.attrib.get('ServerList') is not None:
                to = _getServerListValue(to.attrib.get('ServerList'), running_servers);
            else:
                to = to.text;
                
            result.append((needle, to))
        
    return result;

def _execute(root, debug):
    print('==============================')
    print('        Enter '+_commandName)
    print('==============================')

    timeout = root.attrib.get('Timeout', 60)
    env_file = _checked_get(root, 'TestEnv', _commandName)
    suite_file = _checked_get(root, 'TestSuite', _commandName)
    output_prefix  = _checked_get(root, 'Prefix', _commandName)
    touchstone_binary = _checked_get(root, 'Touchstone', _commandName)
    replacement_tag = _checked_get(root,'ReplacementTag',_commandName)
    cwd = _checked_get(root, 'cwd', _commandName)
    dm_encoding = root.attrib.get("DMEncoding")
    
    servers = _get_servers(root)

    _logger.info("servers={0} timeout={1} env_file={2} suite_file={3} output_prefix={4} touchstone_binary={5} cwd={6} dm_encoding={7}".format(servers, timeout, env_file, suite_file, output_prefix, touchstone_binary, cwd, dm_encoding))
    
    started_servers = []
    try:
        _start_servers(servers, started_servers, debug)
        if not debug:
            running_servers = _get_running_servers(started_servers, timeout, debug)
            _update_suite_file(suite_file, replacement_tag, running_servers, _getExtraReplacements(root, running_servers))
        outdir = cwd + '/test_output'
        if not TouchstoneTestList.RunOneTestSuite(env_file, suite_file, output_prefix, touchstone_binary, cwd=cwd, outdir=outdir, dm_encoding=dm_encoding):
            raise RuntimeError("Could not find testsuite '{0}'!".format(suite_file))
        TouchstoneTestList.CopyTouchstoneOutputToDestination(outdir)
    except (AttributeError, SyntaxError):
        # Prevent code higher up the stack from ignoring these types of exceptions by wrapping them.
        t, value, tb = sys.exc_info()
        raise RuntimeError(str(t) + ': ' + str(value) + '\n' + str(traceback.extract_tb(tb)))
    except:
        if not debug:
            _stop_servers(started_servers)
        raise
        
    if not debug:
        _stop_servers(started_servers)
    
def _get_servers(root):
    result = []
    names = set()
    for server in _checked_find(root, 'Servers', _commandName):
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
            
        result.append(ServerDescription(name, path, parameters))
        names.add(name)
    return result
    
def _start_servers(servers, started_servers, debug):
    for description in servers:
        if not debug:
            removeSingleFile(_get_listen_address_file_name(description.name))
        BackgroundCommand.run(description.name, [description.path] + description.parameters, isDebug=debug)
        started_servers.append(description.name)
    
def _get_running_servers(started_servers, timeout, debug):
    result = []
    if not debug:
        files = [_get_listen_address_file_name(name) for name in started_servers]
        CheckFileExists.Run(files, timeout=timeout)
        
        for name, path in zip(started_servers, files):
            with open(path) as f:
                first_line = f.readline()
                components = first_line.split()
                address = components[0]
                port = components[1]
                
                result.append(RunningServer(name, address, port))
            
    return result
    
def _update_suite_file(suite_file, replacement_tag, running_servers, extra_replacements):
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

    ReplaceInFile.replace(suite_file, '<'+replacement_tag+'/>', replacement)
    
    # TODO: Make this more efficient than doing a whole-file replacement multiple times
    for needle, replacement in extra_replacements:
        ReplaceInFile.replace(suite_file, needle, replacement)
    
def _stop_servers(started_servers):
    for server in started_servers:
        Shared.BackgroundCommands.stop(server)
        
def _get_listen_address_file_name(name):
    return os.path.abspath("{0}_ListenAddresses.txt".format(name))
