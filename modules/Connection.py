import requests
import logging
import json

from urllib3 import disable_warnings
from urllib3 import exceptions
from singleton_decorator import singleton

LOG = logging.getLogger('apic_exporter.exporter')
TIMEOUT = 15

@singleton
class SessionPool(object):

    def __init__(self, targets, user, password):
        self.sessions = {}
        for target in targets:
            self.sessions[target] = {}
            self.sessions[target]['token'], self.sessions[target]['sessionId'] = self.requestToken(target, user=user, password=password)

    def setToken(self,target, token, sessionId):
        self.sessions[target]['token']     = token
        self.sessions[target]['sessionId'] = sessionId

    def getToken(self, target):
        return self.sessions[target]['token'], self.sessions[target]['sessionId']

    def requestToken(self, target, **kwargs):
        disable_warnings(exceptions.InsecureRequestWarning)
        proxies = {'https': '', 'http': '', 'no': '*'}

        user     = kwargs.pop('user', None)
        password = kwargs.pop('password', None)
        refresh  = kwargs.pop('refresh', False)

        if refresh:
            LOG.info("Refresh token for %s", target)
        else:
            LOG.info("Request token for %s", target)

        try:
            if refresh:
                url = "https://" + target + "/api/aaaRefresh.json?"
                resp = requests.get(url, proxies=proxies, verify=False, timeout=TIMEOUT)
            else:
                url = "https://" + target + "/api/aaaLogin.json?"
                payload = {"aaaUser": {"attributes": {"name": user, "pwd": password}}}
                resp = requests.post(url, json=payload, proxies=proxies, verify=False, timeout=TIMEOUT)
        except ConnectionError as e:
            LOG.error("Cannot connect to %s: %s", url, e)
            return None, None
        except TimeoutError as e:
            LOG.error("Connection with host %s timed out", target)
            return None, None

        token, seesionId = None, None
        if resp.status_code == 200:
            res = json.loads(resp.text)
            resp.close()
            token     = res['imdata'][0]['aaaLogin']['attributes']['token']
            seesionId = res['imdata'][0]['aaaLogin']['attributes']['sessionId']
        else:
            LOG.error("url %s responds with %s", url, resp.status_code)

        return token, seesionId

class Connection():

    def __init__(self, hosts, user, password):
        self.user     = user
        self.password = password
        self.pool     = SessionPool(hosts, user, password)

    def getRequest(self, target, query):
        disable_warnings(exceptions.InsecureRequestWarning)
        proxies  = {'https': '', 'http': '', 'no': '*'}

        url     = "https://" + target + query
        LOG.debug('Submitting request %s', url)

        token, _ = self.pool.getToken(target)
        try:
            sess = requests.Session()
            resp = sess.get(url, cookies={"APIC-cookie": token}, proxies=proxies, verify=False, timeout=TIMEOUT)
        except ConnectionError as e:
            LOG.error("Cannot connect to %s: %s", url, e)
            return None
        except TimeoutError as e:
            LOG.error("Connection with host %s timed out", target)
            return None

        # request a new token
        if resp.status_code == 403 and ("Token was invalid" in resp.text or "token" in resp.text):

            newToken, newSessionId = self.pool.requestToken(target, user=self.user, password=self.password)
            self.pool.setToken(target, newToken, newSessionId)

            try:
                resp = requests.get(url, cookies={"APIC-cookie": newToken}, proxies=proxies, verify=False, timeout=TIMEOUT)
            except ConnectionError as e:
                LOG.error("Cannot connect to %s: %s", url, e)
                return None
            except TimeoutError as e:
                LOG.error("Connection with host %s timed out", target)
                return None

        if resp.status_code == 200:
            res = json.loads(resp.text)
            resp.close()
            return res
        else:
            LOG.error("url %s responding with %s", url, resp.status_code)
            return None

    def isDataValid(self, data):
        if data is None:
            return False
        if isinstance(data, dict) and isinstance(data.get('imdata'), list):
            return True
        return False