from __future__ import print_function
import os
import platform
import Command
import Remove
from BoosterError import FileNotFoundError, BoosterError
import ata.log

logger = ata.log.AtaLog(__name__)


def _doExecute(root, isDebug):
    print('==============================')
    print('       Enter TrustStore')
    print('==============================')

    certificate = getCertificate(root)
    action = getAction(root)
    current_platform = getPlatform(root)
    current_distribution = getDistribution()
    command = getCommand(certificate, action, current_platform, current_distribution)

    if not isDebug:
        for cmd in command:
            Command.ExecuteAndLogVerbose(cmd)
    else:
        for cmd in command:
            logger.info(cmd)


def Execute(root):
    _doExecute(root, False)


def Debug(root):
    _doExecute(root, True)


def getCertificate(root):
    return root.text


def getAction(root):
    return root.attrib.get('action', 'install')


def getPlatform(root):
    if root.attrib.get('jre','') != '':
        return root.attrib.get('jre','')
    else:
        return os.environ.get('BOOSTER_VAR_PLATFORM','')


def getDistribution():
    return platform.linux_distribution()


def getCommand(certificate, action, platform, distribution):
    if platform == 'Windows':
        return getWindowsCommand(certificate, action)
    if platform == 'Linux':
        return getLinuxCommand(certificate,action,distribution)
    if platform == 'OSX':
        return getOSXCommand(certificate,action)
    if 'jre' in platform:
        return getJavaCommand(certificate,action, platform)


def getWindowsCommand(certificate, action):
    commandlist=[]
    if action == 'install':
        command = 'certutil -addstore -enterprise -f "Root" ' +  certificate
        commandlist.append(command)
    elif action == 'uninstall':
        command =  'certutil -delstore -enterprise "Root" ' + certificate
        commandlist.append(command)
    else:
        command = 'echo certutil ' + action + ' is not supported'
        commandlist.append(command)
    return commandlist


def getJavaCommand(certificate, action, jre):
    keytoolPath = getJavaKeyTool(jre)
    commandlist=[]
    cwd = os.environ.get('BOOSTER_VAR_STAGING_DIR', os.getcwd())
    Remove.removeSingleFile(cwd + '/' + jre + '.keystore')
    if action == 'install':
        command = 'echo yes|' + keytoolPath + ' -importcert -alias ' + os.path.basename(certificate) + ' -file ' + certificate +' -keystore ' + cwd + '/' + jre + '.keystore ' + '-storepass 123456789 -trustcacerts'
        commandlist.append(command)
        command = keytoolPath + ' -list -v -keystore ' + cwd + '/' + jre + '.keystore ' + '-storepass 123456789'
        commandlist.append(command)
    elif action == 'uninstall':
        command =  keytoolPath + ' -delete -alias ' + os.path.basename(certificate) + ' -keystore ' + cwd + '/' + jre + '.keystore ' + '-storepass 123456789'
        commandlist.append(command)
    else:
        command = 'echo keytool ' + action + ' is not supported'
        commandlist.append(command)
    return commandlist


def getJavaKeyTool(jre):
    jre=jre.upper()
    jdk = jre.replace('JRE', 'JDK')
    bitness = os.environ.get('BOOSTER_VAR_BITNESS', '64')
    if bitness == '64':
        javaHome = os.environ.get('BOOSTER_VAR_' + jdk + '_HOME')
    else:
        javaHome = os.environ.get('BOOSTER_VAR_' + jdk + '_HOME32')
    # if agent doesn't match global settings, give a warning and use capability
    if not os.path.exists(javaHome):
        logger.warning('standard java home does not exist, check capability')
        if bitness == '64':
            javaHome = os.environ.get('BAMBOO_CAPABILITY_SYSTEM_JDK_' + jdk + 'x64',
                                      os.environ.get('bamboo_capability_system_jdk_' + jdk + 'x64', 'undef'))
        else:
            javaHome = os.environ.get('BAMBOO_CAPABILITY_SYSTEM_JDK_' + jdk + 'x86',
                                      os.environ.get('bamboo_capability_system_jdk_' + jdk + 'x86', 'undef'))
    return '"' + javaHome + '/bin/keytool' + '"'


def getLinuxCommand(certificate,action,distribution):
    commandlist = []
    if 'CentOS' in distribution[0] or 'Red Hat' in distribution[0]:
        if '5.' in distribution[1]:
            commandlist = getEL5Command(certificate,action)
        else:
            commandlist = getELCommand(certificate,action)
    elif distribution[0] == 'debian' or distribution[0] == 'Ubuntu':
        commandlist = getDBCommand(certificate,action)
    elif distribution[0] == 'SUSE Linux Enterprise Server':
        commandlist = getSUSECommand(certificate,action)
    else:
        command = 'echo unsupported Linux version ' + distribution[0]
        commandlist.append(command)
        command = 'echo The module support CentOS, RedHat, Oracle, Debian, Ubuntu and Suse Linux'
        commandlist.append(command)
    return commandlist


def getEL5Command(certificate,action):
    commandlist = []
    if action == 'install':
        command = 'echo install ' + certificate + ' for EL5'
        commandlist.append(command)
        command = 'sudo chmod 0777 /etc/pki/tls/certs/ca-bundle.crt'
        commandlist.append(command)
        command = 'sudo openssl x509 -in ' + certificate + ' -noout -text>>/etc/pki/tls/certs/ca-bundle.crt'
        commandlist.append(command)
        command = 'cat ' + certificate + ' >>/etc/pki/tls/certs/ca-bundle.crt'
        commandlist.append(command)
        command = 'sudo chmod 0644 /etc/pki/tls/certs/ca-bundle.crt'
        commandlist.append(command)
    if action == 'uninstall':
        command = 'echo uninstall ' + certificate + ' for EL5'
        commandlist.append(command)
        command = 'sudo chmod 0777 /etc/pki/tls/certs/ca-bundle.crt'
        commandlist.append(command)
        command = 'cat /etc/pki/tls/certs/ca-bundle.crt.rpmnew >/etc/pki/tls/certs/ca-bundle.crt'
        commandlist.append(command)
        command = 'sudo chmod 0644 /etc/pki/tls/certs/ca-bundle.crt'
        commandlist.append(command)
    return commandlist


def getELCommand(certificate,action):
    commandlist = []
    if action == 'install':
        command = 'echo install ' + certificate + ' for EL6 and above'
        commandlist.append(command)
        command = 'sudo cp -f ' + certificate + ' /etc/pki/ca-trust/source/anchors/'
        commandlist.append(command)
        command = 'sudo update-ca-trust'
        commandlist.append(command)

    if action == 'uninstall':
        command = 'echo uninstall ' + certificate + ' for EL6 and above'
        commandlist.append(command)
        command = 'sudo rm -f /etc/pki/ca-trust/source/anchors/' + os.path.basename(certificate)
        commandlist.append(command)
        command = 'sudo update-ca-trust'
        commandlist.append(command)
    return commandlist


def getDBCommand(certificate,action):
    commandlist = []
    if action == 'install':
        command = 'echo install ' + certificate + ' for Dabian Linux'
        commandlist.append(command)
        command = 'rename .pem .crt ' + certificate.replace('.pem','.crt')
        commandlist.append(command)
        command = 'sudo cp -f ' + certificate.replace('.pem','.crt') + ' /etc/pki/ca-trust/source/anchors/'
        commandlist.append(command)
        command = 'sudo update-ca-certificates'
        commandlist.append(command)

    if action == 'uninstall':
        command = 'echo uninstall ' + certificate + ' for Dabian Linux'
        commandlist.append(command)
        command = 'sudo rm -f /etc/pki/ca-trust/source/anchors/' + os.path.basename(certificate).replace('.pem','.crt')
        commandlist.append(command)
        command = 'sudo update-ca-certificates'
        commandlist.append(command)
    return commandlist


def getSUSECommand(certificate,action):
    commandlist = []
    if action == 'install':
        command = 'echo install ' + certificate + ' for Suse Linux is not supported yet'
        commandlist.append(command)

    if action == 'uninstall':
        command = 'echo uninstall ' + certificate + ' for Suse Linux is not supported yet'
        commandlist.append(command)
    return commandlist






