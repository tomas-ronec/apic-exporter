import requests
import logging
import json

from urllib3 import disable_warnings
from urllib3 import exceptions

LOG = logging.getLogger('apic_exporter.exporter')
TIMEOUT = 15

class Connection():

    def __init__(self, hosts, user, password):
        self.user = user
        self.password = password
        self.cookies = {}
        for host in hosts:
            self.cookies[host] = self.getCookie(host, self.user, self.password)

    def getCookie(self, target, user, password):
        disable_warnings(exceptions.InsecureRequestWarning)
        proxies = {'https': '', 'http': '', 'no': '*'}
        LOG.debug("Request cookie for %s", target)

        url     = "https://" + target + "/api/aaaLogin.json?"
        payload = {"aaaUser":{"attributes": {"name": user, "pwd": password}}}

        try:
            resp = requests.post(url, json=payload, proxies=proxies, verify=False, timeout=TIMEOUT)
        except ConnectionError as e:
            LOG.error("Cannot connect to %s: %s", url, e)
            return None
        except TimeoutError as e:
            LOG.error("Connection with host %s timed out", target)
            return None

        cookie = None
        if resp.status_code == 200:
            res = json.loads(resp.text)
            resp.close()
            cookie = res['imdata'][0]['aaaLogin']['attributes']['token']
        else:
            LOG.error("url %s responds with %s", url, resp.status_code)

        return cookie

    def getRequest(self, target, request):
        disable_warnings(exceptions.InsecureRequestWarning)
        proxies  = {'https': '', 'http': '', 'no': '*'}

        url     = "https://" + target + request
        LOG.debug('Submitting request %s', url)

        try:
            resp = requests.get(url, cookies={"APIC-cookie": self.cookies[target] }, proxies=proxies, verify=False, timeout=TIMEOUT)
        except ConnectionError as e:
            LOG.error("Cannot connect to %s: %s", url, e)
            return None
        except TimeoutError as e:
            LOG.error("Connection with host %s timed out", target)
            return None

        # refresh the cookie
        if resp.status_code == 403 and ("Token was invalid" in resp.text or "token" in resp.text):
            self.cookies[target] = self.getCookie(target, self.user, self.password)

            try:
                resp = requests.get(url, cookies={"APIC-cookie": self.cookies[target]}, proxies=proxies, verify=False, timeout=TIMEOUT)
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