import requests
from requests import cookies
import logging
import json

from urllib3 import disable_warnings
from urllib3 import exceptions
from singleton_decorator import singleton

LOG = logging.getLogger('apic_exporter.exporter')
TIMEOUT = 10

@singleton
class SessionPool(object):

    def __init__(self, targets, user, password):
        self.sessions = {}
        for target in targets:
            self.sessions[target] = {}
            self.sessions[target] = self.createSession(target, user=user, password=password)

    def getSession(self, target):
        return self.sessions[target]

    def createSession(self, target, user, password):
        session = requests.Session()
        session.proxies =  {'https':'', 'http': '', 'no':'*'}
        session.verify = False

        cookie = self.requestCookie(target, session, user=user, password=password)
        session.cookies = cookies.cookiejar_from_dict(cookie_dict={"APIC-cookie": cookie})

        return session
    
    def refreshCookie(self, target, user, password):
        session = self.sessions[target]
        session.cookies.clear_session_cookies()

        cookie = self.requestCookie(target, session, user=user, password=password)
        session.cookies = cookies.cookiejar_from_dict(cookie_dict={"APIC-cookie": cookie}, cookiejar=session.cookies)
        self.sessions[target] = session

        return session

    def requestCookie(self, target, session, **kwargs):
        disable_warnings(exceptions.InsecureRequestWarning)

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
                resp = session.get(url, timeout=TIMEOUT)
            else:
                url = "https://" + target + "/api/aaaLogin.json?"
                payload = {"aaaUser": {"attributes": {"name": user, "pwd": password}}}
                resp = session.post(url, json=payload, timeout=TIMEOUT)
        except ConnectionError as e:
            LOG.error("Cannot connect to %s: %s", url, e)
            return None
        except ( requests.exceptions.ConnectTimeout,  requests.exceptions.ReadTimeout, TimeoutError ) as e:
            LOG.error("Connection with host %s timed out after %s sec", target, TIMEOUT)
            return None

        token = None
        if resp.status_code == 200:
            res = json.loads(resp.text)
            resp.close()
            token     = res['imdata'][0]['aaaLogin']['attributes']['token']
        else:
            LOG.error("url %s responds with %s", url, resp.status_code)

        return token

class Connection():

    def __init__(self, hosts, user, password):
        self.user     = user
        self.password = password
        self.pool     = SessionPool(hosts, user, password)

    def getRequest(self, target, query):
        disable_warnings(exceptions.InsecureRequestWarning)

        url     = "https://" + target + query
        LOG.debug('Submitting request %s', url)

        sess = self.pool.getSession(target)

        try:
            resp = sess.get(url, timeout=TIMEOUT)
        except ConnectionError as e:
            LOG.error("Cannot connect to %s: %s", url, e)
            return None
        except ( requests.exceptions.ConnectTimeout,  requests.exceptions.ReadTimeout, TimeoutError ) as e:
            LOG.error("Connection with host %s timed out after %s sec", target, TIMEOUT)
            return None

        # request a new token
        if resp.status_code == 403 and ("Token was invalid" in resp.text or "token" in resp.text):

            sess = self.pool.refreshCookie(target, self.user, self.password)

            try:
                resp = sess.get(url, timeout=TIMEOUT)
            except ConnectionError as e:
                LOG.error("Cannot connect to %s: %s", url, e)
                return None
            except ( requests.exceptions.ConnectTimeout,  requests.exceptions.ReadTimeout, TimeoutError ) as e:
                LOG.error("Connection with host %s timed out after %s sec", target, TIMEOUT)
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