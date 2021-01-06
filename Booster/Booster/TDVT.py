from __future__ import print_function
import os
import classes.BoosterTag
from Command import ExecuteAndGetResult


class TDVT(classes.BoosterTag.BoosterTag):

    def __init__(self):
        self.PrintBanner()

    def Run(self):
        path = os.environ['TDVTPATH']
        callstr = 'python ' + 'tdvt.py ' + self.args
        current_working_directory = os.getcwd()
        os.chdir(path)
        try:
            ExecuteAndGetResult(callstr, path)
        except Exception as e:
            print('tdvt returned a error code:' + str(e))
        os.chdir(current_working_directory)

    def Execute(self, arguments):
        self.args = arguments
        self.Run()

    def Debug(self, arguments):
        self.args = arguments
        self.Run()


def Execute(root):
    for element in list(root):
        tdvt = TDVT()
        tdvt.Execute(element.text)


def Debug(root):
    for element in list(root):
        tdvt = TDVT()
        tdvt.Debug(element.text)
