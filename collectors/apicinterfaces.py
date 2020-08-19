import logging

from prometheus_client.core import GaugeMetricFamily
import BaseCollector
from modules.Connection import Connection

LOG = logging.getLogger('apic_exporter.exporter')

class ApicInterfacesCollector (BaseCollector.BaseCollector):

    def describe(self):

        yield GaugeMetricFamily('network_apic_physcial_interface_reset_counter', 'APIC physical interface reset counter')

    def collect(self):
        LOG.info('Collecting APIC interface metrics ...')

        # query only reset counters > 0
        query = '/api/node/class/ethpmPhysIf.json?query-target-filter=gt(ethpmPhysIf.resetCtr,"0")'
        for host in self.hosts.keys():
            fetched_data   = Connection.getRequest(host, query, cookie=self.hosts[host]['cookie'], user=self.user, password=self.password)
            if not Connection.isDataValid(fetched_data):
                LOG.error("Skipping apic host %s, %s did not return anything", host, query)
                continue

            g = GaugeMetricFamily('network_apic_physcial_interface_reset_counter',
                                  'APIC physical interface reset counter',
                                  labels=['interfaceID'])

            # physical interface reset counter
            for item in fetched_data['imdata']:

                g.add_metric(labels=[host + "-" + item['ethpmPhysIf']['attributes']['dn']],
                             value=item['ethpmPhysIf']['attributes']['resetCtr'])

            yield g