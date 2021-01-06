from __future__ import print_function
import abc


class BoosterTag(object):
    StartingTag = '='
    NumberOfStartingTag = 30
    EndingTag = '='
    NumberOfEndingTag = 30
    LineLength = 30

    def __init__(self):
        pass

    @abc.abstractmethod
    def Debug(self, arguments):
        pass

    @abc.abstractmethod
    def Execute(self, arguments):
        pass

    def PrintBanner(self):
        print(BoosterTag.StartingTag * BoosterTag.NumberOfStartingTag)
        printMessage = 'Enter ' + self.__class__.__name__
        print(printMessage.center(BoosterTag.LineLength, ' '))
        print(BoosterTag.EndingTag * BoosterTag.NumberOfEndingTag)
