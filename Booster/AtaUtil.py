from __future__ import print_function
import os
import pickle
import re
import unittest


def getSelectedBambooVariables(args, filter):
    """
    Return a subset of args, intersected by filter.
    """
    v = {}
    for key in filter:
        if key in args:
            v[key] = args[key]
    return v


def mergeDict(dst, src, untouch=False):
    if dst is None:
        if isinstance(src, dict):
            return src.copy()
        raise BadTypeException(
            "Type error <%s, %s>: mergeDict arguments should be of dict type." % (type(dst), type(src)))
    if src is None:
        return dst
    if not isinstance(dst, dict) or not isinstance(src, dict):
        raise BadTypeException(
            "Type error <%s, %s>: mergeDict arguments should be of dict type." % (type(dst), type(src)))
    for key in src:
        if not (untouch and key in dst):
            dst[key] = src[key]
    return dst


def print_env():
    print("---------- environment --------------")
    for key in sorted(os.environ.keys()):
        print("    %s=%s" % (key, os.environ[key]))
    print("-------------------------------------")


def log_env(logfile):
    with open(logfile, 'w') as fhandle:
        for key in sorted(os.environ.keys()):
            fhandle.write("%s=%s\n" % (key, os.environ[key]))


def setupFakeBambooEnv():
    env = {}
    with open('win_x64_bamboo_test_env.txt', 'r') as fhandle:
        for line in fhandle:
            key_val = line.strip().split("=")
            if len(key_val) == 2:
                key, val = key_val
                key = key.replace(" ", "")
                os.environ[key] = val
                env[key] = val
    return env


class BadTypeException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


def pickle_obj(obj, outfile):
    with open(outfile, 'wb') as fhandle:
        pickle.dump(obj, fhandle)


def normalize_path(path, win_hostname='oak.simba.ad'):
    """
    Returns normalized paths for windows and unix
    :param path: (str) file path
    :param win_hostname: hostname used in UNC path (defaults to oak.simba.ad)
    :return: tuple containing the windows and unix paths
    """
    unc_match = match_unc_path(path)
    if unc_match:
        hostname = unc_match.group(1)
        file_path_group = unc_match.group(2)
        file_path = file_path_group.replace('/', '\\')
        win_path = '\\\\{hostname}{file_path}'.format(hostname=hostname, file_path=file_path)
        unix_path = '/mnt{}'.format(file_path.replace('\\', '/'))
    else:
        unix_path = path.replace('\\', '/')
        win_path = re.sub('^/mnt', r'\\\\{}'.format(win_hostname), unix_path)
        win_path = win_path.replace('/', '\\')
    return win_path, unix_path


def match_unc_path(path):
    """
    Matches a windows UNC path
    :param path: (str) a file path
    :return: Match object
    """
    pattern = r'^//(\w+\.\w+\.\w+)(.*)'
    return re.match(pattern, path)


def fix_booster_path(path, environment, recursive=False):
    """
    Replaces $(...) variables with the actual value
    :param path: file/directory path
    :param environment: dict containing values for the variables
    :param recursive: If set to True, variables are replaced recursively
    :return: a path with variables replaced by actual values
    """
    variable_pattern = r'\$\((.*?)\)'
    found_variables = re.findall(variable_pattern, path)
    for variable in found_variables:
        booster_variable = "BOOSTER_VAR_" + variable
        if variable in environment:
            value = environment.get(variable, "?{}?".format(variable))
        elif booster_variable in environment:
            value = environment.get(booster_variable, "?{}?".format(variable))
        else:
            value = "?{}?".format(variable)
        path = path.replace('$({})'.format(variable), value)
    if recursive and found_variables:
        return fix_booster_path(path, environment, recursive)
    return path


class TestAtaUtil(unittest.TestCase):
    def test_merge_dict(self):
        d1 = {'a': 1, 'b': 2, 'c': 3}
        d2 = {'c': 4, 'd': 5}
        expectedMerge = {'a': 1, 'b': 2, 'c': 4, 'd': 5}
        actualMerge = mergeDict(d1, d2)
        self.assertEqual(actualMerge, expectedMerge, "mergeDict failed")

    def test_normalize_build_paths(self):
        """
        Ensures paths are normalized properly
        """
        win_path = "//oak.simba.ad/builds/Drivers/MySQLODBC/1.0/compile/" \
                   "head__CL333245_SEN_SimbaEngineSDK_10.1.6.1048_Internal/MySQLODBC_w2012r2_vs2015_64.zip"
        unix_path = "/mnt/builds/Drivers/MySQLODBC/1.0/compile/" \
                    "head__CL333245_SEN_SimbaEngineSDK_10.1.6.1048_Internal/MySQLODBC_w2012r2_vs2015_64.zip"
        expected_win_path = r'\\oak.simba.ad\builds\Drivers\MySQLODBC\1.0\compile' \
                            '\head__CL333245_SEN_SimbaEngineSDK_10.1.6.1048_Internal\MySQLODBC_w2012r2_vs2015_64.zip'
        expected_unix_path = "/mnt/builds/Drivers/MySQLODBC/1.0/compile/" \
                             "head__CL333245_SEN_SimbaEngineSDK_10.1.6.1048_Internal/MySQLODBC_w2012r2_vs2015_64.zip"
        actual_win_path, actual_unix_path = normalize_path(win_path)
        self.assertEqual(expected_win_path, actual_win_path)
        self.assertEqual(expected_unix_path, actual_unix_path)
        actual_win_path, actual_unix_path = normalize_path(unix_path)
        self.assertEqual(expected_win_path, actual_win_path)
        self.assertEqual(expected_unix_path, actual_unix_path)

    def test_normalize_build_paths(self):
        """
        Ensures paths are normalized properly
        """
        win_path = "//oak.simba.ad/builds/Drivers/MySQLODBC/1.0/compile/" \
                   "head__CL333245_SEN_SimbaEngineSDK_10.1.6.1048_Internal/MySQLODBC_w2012r2_vs2015_64.zip"
        unix_path = "/mnt/builds/Drivers/MySQLODBC/1.0/compile/" \
                    "head__CL333245_SEN_SimbaEngineSDK_10.1.6.1048_Internal/MySQLODBC_w2012r2_vs2015_64.zip"
        expected_win_path = r'\\oak.simba.ad\builds\Drivers\MySQLODBC\1.0\compile' \
                            '\head__CL333245_SEN_SimbaEngineSDK_10.1.6.1048_Internal\MySQLODBC_w2012r2_vs2015_64.zip'
        expected_unix_path = "/mnt/builds/Drivers/MySQLODBC/1.0/compile/" \
                             "head__CL333245_SEN_SimbaEngineSDK_10.1.6.1048_Internal/MySQLODBC_w2012r2_vs2015_64.zip"
        actual_win_path, actual_unix_path = normalize_path(win_path)
        self.assertEqual(expected_win_path, actual_win_path)
        self.assertEqual(expected_unix_path, actual_unix_path)
        actual_win_path, actual_unix_path = normalize_path(unix_path)
        self.assertEqual(expected_win_path, actual_win_path)
        self.assertEqual(expected_unix_path, actual_unix_path)

    def test_replace_booster_var(self):
        path = '$(PACKAGEDIR)/$(PACKAGENAME).zip'
        package_dir = '//oak.simba.ad/builds/Drivers/CassandraJDBC/1.1/package/' \
                      'head__CL334263_SEN_SimbaEngineSDK_10.1.6.1048_Internal/OEM'
        package_name = 'SimbaCassandraJDBC4-0.0.0.9'
        environment = {'PACKAGEDIR': package_dir, 'PACKAGENAME': package_name}
        expected_path = "{package_dir}/{package_name}.zip".format(package_dir=package_dir, package_name=package_name)
        actual_path = fix_booster_path(path, environment)
        self.assertEqual(expected_path, actual_path)

    def test_recursive_replace_booster_var(self):
        environment = {
            "MINOR_V": "1",
            "MAJOR_V": "1",
            "REVISION_V": "0",
            "BUILD_V": "0000",
            "PACKAGEDIR": "//oak.simba.ad/builds/Drivers/CassandraJDBC/1.1/package/head__CL334263_SEN_$(SEN_LABEL)/OEM",
            "PACKAGENAME": "SimbaCassandraJDBC4-$(MAJOR_V).$(MINOR_V).$(REVISION_V).$(BUILD_V)",
            "SEN_LABEL": "SimbaEngineSDK_10.1.7.1060"
        }
        path = '$(PACKAGEDIR)/$(PACKAGENAME).zip'
        package_dir = '//oak.simba.ad/builds/Drivers/CassandraJDBC/1.1/package/' \
                      'head__CL334263_SEN_SimbaEngineSDK_10.1.7.1060/OEM'
        package_name = 'SimbaCassandraJDBC4-1.1.0.0000'
        expected_path = "{package_dir}/{package_name}.zip".format(package_dir=package_dir, package_name=package_name)
        actual_path = fix_booster_path(path, environment, recursive=True)
        self.assertEqual(expected_path, actual_path)


if __name__ == '__main__':
    unittest.main()
