from Booster.Debug import Debug as Debugger
from Booster.Scope import Scope

class Action(object):
    """
    Interface of an action.

    In OOP style, all actions should derive from this class.
    This class gives the template of invoking an action, by calling run() method.

    """
    def __init__(self, root, name='unknown'):
        """
        Constructor
        :param root:            XML node, used to extract children and attributes
        :param name:            name of action
        """
        self.root = root
        self.name = name
        self.skipmsg = None

    def run(self, dry=False):
        """
        Interface to perform an action. Clients should call this method instead of _perform.
        :param dry:     don't take real actions
        :return:        None
        """
        scope = Scope(self.name)
        if not self._setup():
            return
        self._perform(dry)
        self._tear()

    def _setup(self):
        """
        Prepare to perform an action. The default behavior is to check if the action is marked as skipped.

        :return:    continue to perform only when it returns True
        """
        if Debugger().skip(self.name, self.skipmsg):
            return False
        return True

    def _perform(self, dry=False):
        """
        Actual action. Application shouldn't call this method directly, call run instead.
        :param dry:     don't take real actions
        :return:        None
        """
        pass

    def _tear(self):
        """
        Hood called after perform. Not very useful except for tracing
        :return:        None
        """
        pass

