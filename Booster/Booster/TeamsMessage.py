import json
import urllib2
import ata.log
import os
try:
    import ssl
except ImportError:
    print ('request ssl module not found')
    print ('ignorable it for old unix platforms')
    pass

logger = ata.log.AtaLog(__name__)

def _doExecute(root, isDebug):
    print '=============================='
    print '       Enter TeamsMessage'
    print '=============================='
    webhook = getChannelWebhook(root)
    messages = list(root)
    for message in messages:
        if not isDebug:
            if webhook == 'undef':
                logger.info('please specify the webhook of the channel where you want to receive the message')
            else:
                sendMessage(webhook, message.text)
            #runVeracodeDebug(id, pwd)
        else:
            logger.info('sending slack message')


def Execute(root):
    _doExecute(root, False)


def Debug(root):
    _doExecute(root, True)


def getChannelWebhook(root):
    return root.attrib.get('webhook', 'undef')



def sendMessage(webhook, message):
    ssl._create_default_https_context = ssl._create_unverified_context
    logger.info('sending teams message')
    logger.info(message)
    payload = {
        'text': message,
    }
    data = json.dumps(payload)
    request = urllib2.Request(webhook, data, {'Content-Type': 'application/json'})
    try:
        urllib2.urlopen(request)
    except urllib2.HTTPError, e:
        logger.error('HTTPError = ' + str(e.code))
    except urllib2.URLError, e:
        logger.error('URLError = ' + str(e.reason))
    except httplib.HTTPException, e:
        logger.error('HTTPException')