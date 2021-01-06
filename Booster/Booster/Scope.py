

class Scope(object):
    """
    This is a simple scope trace, which can be used to trace
    """
    depth = 0
    def __init__(self, name):
        self.name = name
        indent = '    ' * Scope.depth
        print('{}=============================='.format(indent))
        print('{}          Enter {}'.format(indent, self.name))
        Scope.depth += 1

    def __del__(self):
        Scope.depth -= 1
        indent = '    ' * Scope.depth
        print('{}          Leave {}'.format(indent, self.name))
        print('{}------------------------------'.format(indent))


