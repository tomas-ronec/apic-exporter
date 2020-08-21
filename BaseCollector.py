from abc import ABC, abstractmethod
from modules.Connection import Connection
import logging

LOG = logging.getLogger('apic_exporter.exporter')

class BaseCollector(ABC):

    def __init__(self, config):
        self.user        = config['apic_user']
        self.password    = config['apic_password']
        self.tenant      = config['apic_tenant_name']

        self.hosts = config['apic_hosts'].split(',')
        LOG.info("APIC hosts to fetch MIT data from: %s", config['apic_hosts'])
        self.connection = Connection(self.hosts, self.user, self.password)
#        self.activeHosts = self._getActiveHosts()

    def _getActiveHosts(self):
        actHosts = {}

        query = '/api/node/class/topSystem.json?query-target-filter=eq(topSystem.role,"controller")'
        # get actual APIC host list
        for host in self.hosts:
            cookie = self.connection.getCookie(host, self.user, self.password)
            data   = self.connection.getRequest(host, query)
            if self.connection.isDataValid(data):
                for item in data['imdata']:
                    addr = item['topSystem']['attributes']['oobMgmtAddr']
                    actHosts[addr] = {}
                    actHosts[addr]['mgmtAddress'] = item['topSystem']['attributes']['oobMgmtAddr']
                    actHosts[addr]['address']     = item['topSystem']['attributes']['address']
                    actHosts[addr]['dn']          = item['topSystem']['attributes']['dn']
                    actHosts[addr]['role']        = item['topSystem']['attributes']['role']
                    actHosts[addr]['state']       = item['topSystem']['attributes']['state']
                    actHosts[addr]['loginCookie'] = cookie
            break #

        return {a: b for a, b in actHosts.items() if b['state'] == 'in-service'}

    @abstractmethod
    def describe(self):
        pass

    @abstractmethod
    def collect(self):
        pass
