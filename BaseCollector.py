from abc import ABC, abstractmethod
import logging
from modules.Connection import Connection

LOG = logging.getLogger('apic_exporter.exporter')

class BaseCollector(ABC):

    def __init__(self, config):
        self.user        = config['apic_user']
        self.password    = config['apic_password']
        self.tenant      = config['apic_tenant_name']

        self.hosts = config['apic_hosts'].split(',')
        self.connection = Connection(self.hosts, self.user, self.password)
#        self.activeHosts = self._getActiveHosts()

    def _getActiveHosts(self):
        actHosts = {}

        # get actual APIC host list
        for host in self.hosts:
            cookie = Connection.getCookie(host, self.user, self.password)
            data   = Connection.getRequest(host,
                                           "/api/node/class/topSystem.json?query-target-filter=eq(topSystem.role,\"controller\")",
                                           cookie=cookie,
                                           user=self.user,
                                           password=self.password)

            if Connection.isDataValid(data):
                for item in data['imdata']:
                    addr = item['topSystem']['attributes']['oobMgmtAddr']
                    actHosts[addr] = {}
                    actHosts[addr]['mgmtAddress'] = addr
                    actHosts[addr]['loginCookie'] = cookie
                break

        # get APIC host mode
        for addr in actHosts.keys():
            data   = Connection.getRequest(actHosts[addr]['mgmtAddress'],
                                           "/api/node/class/infraSnNode.json",
                                           cookie=actHosts[addr]['loginCookie'],
                                           user=self.user,
                                           password=self.password)

            if Connection.isDataValid(data):
                for item in data['imdata']:
                    _addr = (item['infraSnNode']['attributes']['oobIpAddr']).split("/")[0]
                    if _addr in actHosts.keys():
                        actHosts[_addr]['apicMode'] = item['infraSnNode']['attributes']['apicMode']

        return {a: b for a, b in actHosts.items() if b['apicMode'] == 'active'}

    @abstractmethod
    def describe(self):
        pass

    @abstractmethod
    def collect(self):
        pass
