from Collector import Collector
import logging
from prometheus_client.core import GaugeMetricFamily
from typing import List, Dict

LOG = logging.getLogger('apic_exporter.exporter')


class ApicLeafCapacityCollector(Collector):

    def __init__(self, config: Dict):
        super().__init__('apic_leaf_capacity', config)

    def describe(self):
        yield GaugeMetricFamily('network_apic_leaf_capacity',
                                'ACI Leaf capacity')

    def get_query(self) -> str:
        return '/api/class/eqptcapacityEntity.json?query-target=self' + \
               '&rsp-subtree-include=stats&rsp-subtree-class=eqptcapacityL3RemoteUsageCap5min,' + \
               'eqptcapacityL3TotalUsageCap5min,eqptcapacityL3Usage5min,eqptcapacityL3TotalUsage5min,' + \
               'eqptcapacityL2Usage5min,eqptcapacityL2RemoteUsage5min,eqptcapacityL2TotalUsage5min'

    def get_metrics(self, host: str, data: Dict) -> List[GaugeMetricFamily]:
        """Collect the number of EPs and TCAM usage on all leaf switches"""
        g_leaf_cap_tcam = GaugeMetricFamily('network_apic_leaf_capacity_tcam',
                                            'ACI Leaf IPv4 EndPoint TCAM capacity available',
                                            labels=['aciLeaf', 'usage', 'layer'])

        for leaf in data['imdata']:
            if leaf['eqptcapacityEntity']['children']:
                """Ignore spine switches without children data"""
                leaf_data = leaf['eqptcapacityEntity']['children']
                leaf_dn = leaf['eqptcapacityEntity']['attributes']['dn'].split('/')
                leaf_id = leaf_dn[2]
            for data_object in leaf_data:
                if 'eqptcapacityL3TotalUsageCap5min' in data_object:
                    l3_max = data_object['eqptcapacityL3TotalUsageCap5min']['attributes']['v4TotalEpCapMax']
                    g_leaf_cap_tcam.add_metric(labels=[leaf_id, 'max', 'l3'],
                                               value=l3_max)
                elif 'eqptcapacityL3TotalUsage5min' in data_object:
                    l3_total = data_object['eqptcapacityL3TotalUsage5min']['attributes']['v4TotalEpAvg']
                    g_leaf_cap_tcam.add_metric(labels=[leaf_id, 'total', 'l3'],
                                               value=l3_total)
                elif 'eqptcapacityL3Usage5min' in data_object:
                    l3_local = data_object['eqptcapacityL3Usage5min']['attributes']['v4LocalEpAvg']
                    g_leaf_cap_tcam.add_metric(labels=[leaf_id, 'local', 'l3'],
                                               value=l3_local)
                elif 'eqptcapacityL3RemoteUsageCap5min' in data_object:
                    l3_remote = data_object['eqptcapacityL3RemoteUsageCap5min']['attributes']['v4RemoteEpCapAvg']
                    g_leaf_cap_tcam.add_metric(labels=[leaf_id, 'remote', 'l3'],
                                               value=l3_remote)
                elif 'eqptcapacityL2TotalUsage5min' in data_object:
                    l2_max = data_object['eqptcapacityL2TotalUsage5min']['attributes']['totalEpCapMax']
                    l2_total = data_object['eqptcapacityL2TotalUsage5min']['attributes']['totalEpAvg']
                    g_leaf_cap_tcam.add_metric(labels=[leaf_id, 'max', 'l2'],
                                               value=l2_max)
                    g_leaf_cap_tcam.add_metric(labels=[leaf_id, 'total', 'l2'],
                                               value=l2_total)
                elif 'eqptcapacityL2Usage5min' in data_object:
                    l2_local = data_object['eqptcapacityL2Usage5min']['attributes']['localEpAvg']
                    g_leaf_cap_tcam.add_metric(labels=[leaf_id, 'local', 'l2'],
                                               value=l2_local)
                elif 'eqptcapacityL2RemoteUsage5min' in data_object:
                    l2_remote = data_object['eqptcapacityL2RemoteUsage5min']['attributes']['remoteEpAvg']
                    g_leaf_cap_tcam.add_metric(labels=[leaf_id, 'remote', 'l2'],
                                               value=l2_remote)

             return [g_leaf_cap_tcam]
