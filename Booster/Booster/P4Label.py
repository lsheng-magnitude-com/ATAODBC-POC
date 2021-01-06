import re
#from BoosterError import BoosterError

class P4Label(object):
    """
    Compare and find a larger label.

    A valid label is either xxxx-n.n.n or xxxx_n.n.n
    where xxxx is any length of string, n.n.n is any number of digits separated by dot

    A valid label is greater than a non-valid label.
    """
    _pattern_parts = re.compile(r'[_-]')

    def __init__(self, text):
        self.value = text
        self.version = P4Label._pattern_parts.split(text)[-1].split('.')

    def __str__(self):
        return self.value

    def __gt__(self, other):
        try:
            if other is None or not isinstance(other, P4Label):
                return True
            len2 = len(other.version)
            for n,v in enumerate(self.version):
                if n >= len2:
                    return True
                result = int(v) - int(other.version[n])
                if result != 0:
                    return result > 0
            return False
        except:                 # bad format
            return False




if __name__ == '__main__':
    t0 = 'perftest-0.9.15'
    test = [
        'perf-0.9.13',
        'perf-0.9.15',
        'perf-0.9.16',
        'perf_1.0.1',
        'perf-0.8.83',
        'perf-0.9',
        'perf-1',
        'perf-0.9.15.1',
        'perf-0.9.223',
        'perf',
        'perf_0.10.1',
        'perf-1.3.5_abc'
    ]

    p0 = P4Label(t0)
    pmax = None
    for t in test:
        try:
            p = P4Label(t)
            if p > p0:
                print('p({}) > p0({})'.format(p, p0))
            else:
                print('p({})   p0({})'.format(p, p0))
            if p > pmax:
                pmax = p
        except Exception as e:
            print('exception: ' + str(e))
    print('pmax={}'.format(pmax))

