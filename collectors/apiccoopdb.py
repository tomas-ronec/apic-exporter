import logging
import BaseCollector
from prometheus_client.core import GaugeMetricFamily, Summary
from typing import List, Dict

LOG = logging.getLogger('apic_exporter.exporter')
REQUEST_TIME = Summary('apic_coop_processing_seconds',
                       'Time spent processing request')


class ApicCoopDbCollector(BaseCollector.BaseCollector):

    def __init__(self, config: Dict):
        super().__init__(config)
        self.__metric_counter = 0

    def describe(self):
        yield GaugeMetricFamily('network_apic_coop_records_total',
                                'APIC COOP DB entries')

    @REQUEST_TIME.time()
    def collect(self):
        LOG.debug('Collecting APIC coop db metrics ...')

        self.__metric_counter = 0

        yield self.collect_apic_coop_db_size()

        LOG.info('Collected %s APIC COOP DB metrics', self.__metric_counter)

    def collect_apic_coop_db_size(self) -> List[GaugeMetricFamily]:
        """Collect the number of entries in the coop db for all spines"""
        g_coop_db = GaugeMetricFamily('network_apic_coop_records_total',
                                      'APIC COOP DB entries',
                                      labels=['apicHost', 'spineDn'])

        query_spines = '/api/node/class/fabricNode.json?query-target-filter=eq(fabricNode.role,"spine")'
        for host in self.hosts:
            fetched_data = self.connection.getRequest(host, query_spines)
            if not self.connection.isDataValid(fetched_data):
                LOG.warning(
                    "Skipping apic host %s, %s did not return anything", host,
                    query_spines)
                continue
            for spine in fetched_data['imdata']:
                spine_attributes = spine['fabricNode']['attributes']
                query_coop_count = '/api/node/mo/' + spine_attributes[
                    'dn'] + '/sys/coop/inst/dom-overlay-1.json?query-target=subtree&target-subtree-class=coopEpRec&rsp-subtree-include=count'
                fetched_data = self.connection.getRequest(
                    host, query_coop_count)
                if not self.connection.isDataValid(fetched_data):
                    LOG.warning(
                        "Skipping apic host %s, %s did not return anything for spine %s",
                        host, query_coop_count, spine_attributes['dn'])
                    continue
                fetched_count = fetched_data['imdata'][0]['moCount']['attributes']['count']

                g_coop_db.add_metric(labels=[host, spine_attributes['dn']],
                                     value=fetched_count)
                self.__metric_counter += 1
            break  # Each host produces the same metrics.
        return g_coop_db
