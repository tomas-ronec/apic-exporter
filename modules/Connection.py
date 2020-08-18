import requests
import logging
import json

from urllib3 import disable_warnings
from urllib3 import exceptions

LOG = logging.getLogger('apic_exporter.exporter')

class Connection:

    def getCookie(target, user, password):
        disable_warnings(exceptions.InsecureRequestWarning)
        proxies = {'https': '', 'http': '', 'no': '*'}

        url     = "https://" + target + "/api/aaaLogin.json?"
        payload = {"aaaUser":{"attributes": {"name": user, "pwd": password}}}

        try:
            resp = requests.post(url, json=payload, proxies=proxies, verify=False, timeout=15)
        except ConnectionError as e:
            logging.error("Cannot connect to %s: %s", url, e)
            return None

        cookie = None
        if resp.status_code == 200:
            res = json.loads(resp.text)
            resp.close()
            cookie = res['imdata'][0]['aaaLogin']['attributes']['token']
        else:
            logging.error("url %s responds with %s", url, resp.status_code)

        return cookie

    def getRequest(target, request, **kwargs):
        disable_warnings(exceptions.InsecureRequestWarning)

        cookie   = kwargs.pop('cookie')
        user     = kwargs.pop('user')
        password = kwargs.pop('password')
        proxies  = {'https': '', 'http': '', 'no': '*'}

        url     = "https://" + target + request
        LOG.debug('Submitting request %s', url)

        try:
            resp = requests.get(url, cookies={"APIC-cookie": cookie}, proxies=proxies, verify=False, timeout=15)
        except ConnectionError as e:
            logging.error("Cannot connect to %s: %s", url, e)
            return None

        # refresh the cookie
        if resp.status_code == 403 and ("Token was invalid" in resp.text or "token" in resp.text):
            cookie = Connection.getCookie(target, user, password)

            try:
                resp = requests.post(url, cookies={"APIC-cookie": cookie}, proxies=proxies, verify=False, timeout=15)
            except ConnectionError as e:
                logging.error("Cannot connect to %s: %s", url, e)
                return None

        if resp.status_code == 200:
            res = json.loads(resp.text)
            resp.close()
            return res
        else:
            logging.error("url %s responding with %s", url, resp.status_code)
            return None

    def isDataValid(data):
        if data is None:
            return False
        if isinstance(data, dict) and isinstance(data.get('imdata'), list):
            return True
        return False