from Collector import Collector, CustomMetric
import logging
from prometheus_client.core import GaugeMetricFamily, Metric
from typing import List, Dict, Tuple

LOG = logging.getLogger('apic_exporter.exporter')


class ApicCoopDbCollector(Collector):

    def __init__(self, config: Dict):
        super().__init__('apic_coop', config)

    def describe(self):
        yield GaugeMetricFamily('network_apic_coop_records_total',
                                'APIC COOP DB entries')

    def get_metric_definitions(self) -> List[CustomMetric]:
        metrics = []

        metrics.append(CustomMetric(
                name='network_apic_coop_records_total',
                query='/api/node/class/fabricNode.json?query-target-filter=eq(fabricNode.role,"spine")',
                process_data=self.collect_apic_coop_db_size))

        return metrics

    def collect_apic_coop_db_size(self, host: str, data: Dict) -> Tuple[Metric, int]:
        """Collect the number of entries in the coop db for all spines"""
        g_coop_db = GaugeMetricFamily('network_apic_coop_records_total',
                                      'APIC COOP DB entries',
                                      labels=['apicHost', 'spineDn'])
        metric_counter = 0

        for spine in data['imdata']:
            spine_attributes = spine['fabricNode']['attributes']
            query_coop_count = '/api/node/mo/' + \
                               spine_attributes['dn'] + \
                               '/sys/coop/inst/dom-overlay-1.json' + \
                               '?query-target=subtree&target-subtree-class=coopEpRec&rsp-subtree-include=count'
            fetched_data = self.query_host(host, query_coop_count)
            if fetched_data is None:
                return None
            fetched_count = fetched_data['imdata'][0]['moCount']['attributes']['count']
            g_coop_db.add_metric(labels=[host, spine_attributes['dn']],
                                 value=fetched_count)
            metric_counter += 1
        return g_coop_db, metric_counter
