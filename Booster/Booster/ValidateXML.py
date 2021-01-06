import os
import subprocess
import traceback

import ata.log
from BoosterError import FileNotFoundError, BoosterError

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('     Enter ValidateXML')
    print('==============================')
    sources = get_source_list(root)
    java_exe = get_javaexe(root)
    validator = get_validator(root)
    logger.info("javaexe = {}".format(java_exe))
    logger.info("validator = {}".format(validator))
    results = []
    for source in sources:
        source = os.path.normpath(source)
        if os.path.isdir(source):
            results += validate_in_dirs(source, java_exe, validator)
        elif os.path.exists(source):
            results += [validate(java_exe, validator, source)]
        else:
            raise FileNotFoundError(__name__, source)
    invalid = filter(lambda res: res[2] != 0, results)
    if invalid:
        message = "This build contains invalid XML files.\n{errors}\n".format(
            errors='\n'.join(result[1] for result in invalid))
        raise BoosterError(__name__, message)


def Debug(root):
    print('==============================')
    print('     Enter ValidateXML')
    print('==============================')
    sources = get_source_list(root)
    java_exe = root.attrib.get('javaexe', '')
    validator = root.attrib.get('validator', '')
    logger.info("javaexe = {}".format(java_exe))
    logger.info("validator = {}".format(validator))

    for source in sources:
        if os.path.isdir(source):
            logger.info("Validating XML files under directory {}".format(source))
        elif os.path.exists(source):
            logger.info("Validating {}".format(source))


def get_source_list(root):
    elements = list(root)
    sources = []
    for element in elements:
        source = element.text
        sources.append(source)
    return sources


def get_validator(root):
    validator = root.attrib.get('validator', None)
    if not validator:
        # Use the default validator, set in the BTA_XMLVALIDATOR variable in Config/Common/BTA.settings
        validator = os.environ.get('BOOSTER_VAR_BTA_XMLVALIDATOR', '')
    if validator == '':
        raise BoosterError(__name__, "Not default validator to use.")
    if not os.path.exists(validator):
        raise FileNotFoundError(__name__, "{} was not found.".format(validator))
    return os.path.normpath(validator)


def get_javaexe(root):
    java_exe = root.attrib.get('javaexe', None)
    if not java_exe:
        # JDK8 is the default version for the BTA XMLValidator (//ATA/BTAUtils/XMLValidator/target/XMLValidator.jar)
        java_home = os.environ.get('BOOSTER_VAR_JDK1_8_HOME', None)
        if not java_home or not os.path.exists(java_home):
            java_exe = 'java'
        else:
            java_exe = os.path.join('"{}"'.format(java_home), 'bin', 'java')
    return os.path.normpath(java_exe)


def validate_in_dirs(source_dir, java_exe, validator):
    results = []
    for root, dirs, files in os.walk(source_dir):
        xml_files = [source_file for source_file in files if source_file.lower().endswith('.xml')]
        for xml_file in xml_files:
            results.append(validate(java_exe, validator, os.path.join(root, xml_file)))
    if not results:
        raise BoosterError(__name__, 'No XML file to validate under {dir}'.format(dir=source_dir))
    return results


def validate(java_exe, validator, xml):
    command = ' '.join([java_exe, '-jar', validator, xml])
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        logger.info(result.strip())
        return xml, result, 0
    except subprocess.CalledProcessError as error:
        return_code = error.returncode
        output = error.output
        return xml, output, return_code
    except Exception:
        raise BoosterError(__name__, "Unexpected error", traceback.format_exc())
