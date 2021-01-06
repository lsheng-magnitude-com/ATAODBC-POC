from __future__ import print_function
import json
try:
    import urllib2
except ImportError:
    import urllib.request
    import urllib.error
import ata.log
import os
try:
    import ssl
except ImportError:
    print(('request ssl module not found'))
    print(('ignorable it for old unix platforms'))
    pass

logger = ata.log.AtaLog(__name__)

SLACK_HOOK = 'https://hooks.slack.com/services/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'

def _doExecute(root, isDebug):
    print('==============================')
    print('       Enter Slack')
    print('==============================')
    channel = getChannel(root)
    username = getUser(root)
    messages = list(root)
    for message in messages:
        if not isDebug:
            sendMessage(channel, username, message.text)
            #runVeracodeDebug(id, pwd)
        else:
            logger.info('sending slack message')


def Execute(root):
    _doExecute(root, False)


def Debug(root):
    _doExecute(root, True)


def getChannel(root):
    return root.attrib.get('channel', '#ata_slack_test')


def getUser(root):
    return root.attrib.get('user', 'bamboo')


def sendMessage(channel, username, message):
    ssl._create_default_https_context = ssl._create_unverified_context
    logger.info('sending slack message')
    logger.info(message)
    payload = {
        'channel': channel,
        'username': username,
        'link_names': True,
        'text': message,
    }
    data = json.dumps(payload)
    request = urllib2.Request(SLACK_HOOK, data, {'Content-Type': 'application/json'})
    try:
        urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        logger.error('HTTPError = ' + str(e.code))
    except urllib2.URLError as e:
        logger.error('URLError = ' + str(e.reason))
    except httplib.HTTPException as e:
        logger.error('HTTPException')
