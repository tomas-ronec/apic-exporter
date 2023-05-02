from Collector import Collector
import logging
from prometheus_client.core import GaugeMetricFamily
from typing import List, Dict

LOG = logging.getLogger('apic_exporter.exporter')


class ApicFaultsCollector(Collector):

    def __init__(self, config: Dict):
        super().__init__('apic_faults', config)
        self.leaf_ids = {}
        self.gen1_leaves = {}

    def describe(self):
        yield GaugeMetricFamily('network_apic_faults',
                                'APIC faults')

    def get_query(self) -> str:
        return '/api/node/class/faultInst.json?' + \
               'query-target-filter=or(eq(faultInst.lc,"raised"),eq(faultInst.lc,"soaking"))'

    def get_metrics(self, host: str, data: Dict) -> List[GaugeMetricFamily]:
        """Collect and sort APIC Faults by type, severity, domain and acknowledgement"""
        g_apic_faults = GaugeMetricFamily('network_apic_faults_severity',
                                          'APIC faults by severity, type and domain',
                                          labels=['severity', 'type', 'domain', 'ack'])

        faults = {}
        for fault_object in data['imdata']:
            try:
                attrs = unpack(fault_object, 'faultInst', 'attributes')
                key = tuple(unpack(attrs, x)
                            for x in ('severity', 'type', 'domain', 'ack'))
                faults[key] = faults.get(key, 0) + 1
            except ValueError as e:
                LOG.error(
                    f"faultCollector: invalid path {e} in {fault_object}")

        for k, v in faults.items():
            g_apic_faults.add_metric(labels=k,
                                     value=v)
        return [g_apic_faults]


def unpack(data, *keys):
    for k in keys:
        if isinstance(data, dict) and data.get(k):
            data = data[k]
        else:
            return ValueError(f"{keys} not found in data")
    return data

