import logging

from prometheus_client.core import GaugeMetricFamily
import BaseCollector

LOG = logging.getLogger('apic_exporter.exporter')

class ApicInterfacesCollector (BaseCollector.BaseCollector):

    def describe(self):

        yield GaugeMetricFamily('network_apic_physcial_interface_reset_counter', 'APIC physical interface reset counter')

    def collect(self):
        LOG.info('Collecting APIC interface metrics ...')

        g = GaugeMetricFamily('network_apic_physcial_interface_reset_counter',
                              'APIC physical interface reset counter',
                              labels=['apicHost','interfaceID'])

        # query only reset counters > 0
        query = '/api/node/class/ethpmPhysIf.json?query-target-filter=gt(ethpmPhysIf.resetCtr,"0")'
        for host in self.hosts:
            fetched_data   = self.connection.getRequest(host, query)
            if not self.connection.isDataValid(fetched_data):
                LOG.error("Skipping apic host %s, %s did not return anything", host, query)
                continue

            # physical interface reset counter
            for item in fetched_data['imdata']:

                g.add_metric(labels=[host, item['ethpmPhysIf']['attributes']['dn']],
                             value=item['ethpmPhysIf']['attributes']['resetCtr'])

        yield g