from __future__ import print_function
"""Stop a background command started with the BackgroundCommand task"""

__all__ = ['Execute', 'Debug']

import ata.log
from Booster.Shared import BackgroundCommands

logger = ata.log.AtaLog(__name__)


def _do_execute(root, isDebug):
    print('==============================')
    print('        Enter StopBackgroundCommand')
    print('==============================')

    name = root.text
    if name is None:
        raise RuntimeError("Name must be provided!")
    try:
        timeout = int(root.get('timeout', 5))
    except ValueError as e:
        logger.warning('attribute timeout should be a number of seconds ({})'.format(e))
        timeout = 5
    kwargs = {'timeout': timeout}
    sig = root.get('signal')
    if sig:
        kwargs['sig'] = sig

    logger.info('name={name} timeout={timeout}{others}'.format(
        name=name, timeout=timeout, others=(' signal=' + sig) if sig else ''))
    if not isDebug:
        BackgroundCommands.stop(name, **kwargs)


def Execute(root):
    _do_execute(root, False)


def Debug(root):
    _do_execute(root, True)
