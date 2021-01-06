from __future__ import print_function
import json
try:
    import urllib2
except ImportError:
    import urllib.request
    import urllib.error


import ata.log

logger = ata.log.AtaLog(__name__)


class RESTClient(object):
    def post(self, base, rest, args):
        url = self._setup_url(base, rest)
        # print("rest post url=%s" % url)
        logger.debug("rest post url=%s" % url)
        response = self._make_request(url, action="POST", args=args)
        return response

    def get(self, base, rest):
        url = self._setup_url(base, rest)
        logger.debug("rest get url={url}".format(url=url))
        response = self._make_request(url, action="GET")
        return response

    def _setup_url(self, base, rest):
        if base is None:
            return ''  # skip silently in this case
        url = base + rest
        return url

    def _make_request(self, url, action="GET", args=dict()):
        if action == "GET":
            request = urllib2.Request(url)
        elif action in ("PUT", "POST", "DELETE"):
            data = json.dumps(args)
            request = urllib2.Request(url, data, {'Content-Type': 'application/json'})
            if action in ("PUT", "DELETE"):
                request.get_method = lambda: action
        else:
            raise ValueError("Unknown action {action}".format(action=action))
        connection = urllib2.urlopen(request)
        response = connection.read()
        connection.close()
        logger.debug("rest={url} - response={response}".format(url=url, response=response))
        return json.loads(response)
