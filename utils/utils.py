from dateutil import parser
from functools import reduce

def dtime2timestamp(dtime):
    return parser.parse(dtime).timestamp()

def ctime2timestamp(ctime):
    return reduce(lambda x, y: 60.0 * float(x) + float(y), ctime.split(':'), 0.0)

def make_ordinal(n):
    '''
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    '''
    n = int(n)
    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    return str(n) + suffix
