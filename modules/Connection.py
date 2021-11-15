import requests
from requests import cookies
import logging
import json

from urllib3 import disable_warnings
from urllib3 import exceptions
from singleton_decorator import singleton

from typing import List, Dict
from collections import namedtuple

LOG = logging.getLogger('apic_exporter.exporter')
TIMEOUT = 10
COOKIE_TIMEOUT = 5
session_tuple = namedtuple('session_tuple', 'session available')


@singleton
class SessionPool(object):
    def __init__(self, hosts, user, password):
        """Initializes the Session Pool. Sessions contains the session to a host and an Availability flag"""
        self.__sessions = {}
        self.__user = user
        self.__password = password

        for host in hosts:
            self.__sessions[host] = self.createSession(host)

    def getSession(self, host: str) -> session_tuple:
        """Returns the session and availability"""
        return self.__sessions[host]

    def createSession(self, host: str) -> session_tuple:
        """Creates the session and requests the cookie."""
        session = requests.Session()
        session.proxies = {'https': '', 'http': '', 'no': '*'}
        session.verify = False

        cookie = self.requestCookie(host, session)
        if cookie is not None:
            session.cookies = cookies.cookiejar_from_dict(
                cookie_dict={"APIC-cookie": cookie})

        available = True if session is not None and cookie is not None else False

        return session_tuple(session, available)

    def reset_unavailable_hosts(self):
        """Reset availability of all sessions and try to repair unavailable sessions."""
        for host, value in self.__sessions.items():

            if value.session is None:
                self.__sessions[host] = self.createSession(host)
                continue

            if len(value.session.cookies) == 0:
                cookie = self.requestCookie(host, value.session)
                if cookie is not None:
                    value.session.cookies = cookies.cookiejar_from_dict(
                        cookie_dict={"APIC-cookie": cookie})
                    self.__sessions[host] = session_tuple(value.session, True)
                else:
                    self.__sessions[host] = session_tuple(value.session, False)
            else:
                self.__sessions[host] = session_tuple(value.session, True)

    def get_unavailable_sessions(self) -> List[str]:
        return [k for k, v in self.__sessions.items() if not v.available]

    def set_session_unavailable(self, host: str):
        """Set a given host to be unavailable"""
        if host in self.__sessions:
            LOG.debug("Flag host %s as unavailable", host)
            session, _ = self.__sessions[host]
            self.__sessions[host] = session_tuple(session, False)

    def refreshCookie(self, host: str) -> requests.Session:
        """Clears old cookie and requests a fresh one"""
        session, available = self.__sessions[host]

        cookie = self.requestCookie(host, session)

        if cookie is not None:
            session.cookies.clear_session_cookies()
            session.cookies = cookies.cookiejar_from_dict(
                cookie_dict={"APIC-cookie": cookie}, cookiejar=session.cookies)
            available = True
        else:
            available = False

        self.__sessions[host] = session_tuple(session, available)
        return session

    def requestCookie(self, host: str, session: requests.Session) -> str:
        """Login to the host and retrieve cookie"""
        disable_warnings(exceptions.InsecureRequestWarning)

        LOG.info("Request token for %s", host)

        try:
            url = "https://" + host + "/api/aaaLogin.json?"
            payload = {
                "aaaUser": {
                    "attributes": {
                        "name": self.__user,
                        "pwd": self.__password
                    }
                }
            }
            resp = session.post(url, json=payload, timeout=COOKIE_TIMEOUT)
        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout, TimeoutError):
            LOG.error("Connection with host %s timed out after %s sec", host,
                      COOKIE_TIMEOUT)
            return None
        except (requests.exceptions.ConnectionError, ConnectionError) as e:
            LOG.error("Cannot connect to %s: %s", url, e)
            return None

        cookie = None
        if resp.status_code == 200:
            res = json.loads(resp.text)
            resp.close()
            cookie = res['imdata'][0]['aaaLogin']['attributes']['token']
        else:
            LOG.error("url %s responds with %s", url, resp.status_code)

        return cookie


class Connection():
    def __init__(self, hosts: List[str], user: str, password: str):
        self.__pool = SessionPool(hosts, user, password)

    def getRequest(self, host: str, query: str, timeout: int = TIMEOUT) -> Dict:
        """Perform a GET request against host for the query. Retries if token is invalid."""
        disable_warnings(exceptions.InsecureRequestWarning)

        url = "https://" + host + query

        session, available = self.__pool.getSession(host)

        if not available:
            LOG.info("Skipped unavailable host %s query %s", host, query)
            return None

        try:
            LOG.debug('Submitting request %s', url)
            resp = session.get(url, timeout=timeout)
        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout, TimeoutError):
            LOG.error("Connection with host %s timed out after %s sec", host,
                      timeout)
            self.__pool.set_session_unavailable(host)
            return None
        except (requests.exceptions.ConnectionError, ConnectionError) as e:
            LOG.error("Cannot connect to %s: %s", url, e)
            self.__pool.set_session_unavailable(host)
            return None

        # token is invalid, request a new token
        if resp.status_code == 403 and ("Token was invalid" in resp.text
                                        or "token" in resp.text):

            session = self.__pool.refreshCookie(host)

            try:
                resp = session.get(url, timeout=timeout)
            except (requests.exceptions.ConnectTimeout,
                    requests.exceptions.ReadTimeout, TimeoutError):
                LOG.error("Connection with host %s timed out after %s sec",
                          host, timeout)
                self.__pool.set_session_unavailable(host)
                return None
            except (requests.exceptions.ConnectionError, ConnectionError) as e:
                LOG.error("Cannot connect to %s: %s", url, e)
                self.__pool.set_session_unavailable(host)
                return None

        if resp.status_code == 200:
            res = json.loads(resp.text)
            resp.close()
            return res
        else:
            LOG.error("url %s responding with %s", url, resp.status_code)
            return None

    def get_unresponsive_hosts(self) -> List[str]:
        """Returns a list of hosts that were not responding since the last reset."""
        return self.__pool.get_unavailable_sessions()

    def reset_unavailable_hosts(self):
        """Unavailable hosts are repaired and the flags are reset"""
        self.__pool.reset_unavailable_hosts()

    def isDataValid(self, data: Dict):
        """Checks if the data is a dict that contains 'imdata'."""
        if data is None:
            return False
        if isinstance(data, dict) and isinstance(data.get('imdata'), list):
            return True
        return False
