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
        return '/api/class/eqptcapacityEntity.json?query-target=self\
                &rsp-subtree-include=stats&rsp-subtree-class=eqptcapacityL3RemoteUsageCap5min,\
                eqptcapacityL3TotalUsageCap5min,eqptcapacityL3Usage5min,eqptcapacityL3TotalUsage5min,\
                eqptcapacityL2Usage5min,eqptcapacityL2RemoteUsage5min,eqptcapacityL2TotalUsage5min'

    def get_metrics(self, host: str, data: Dict) -> List[GaugeMetricFamily]:
        """Collect the number of EPs and TCAM usage on all leaf switches"""
        g_leaf_cap_tcam_l3_max = GaugeMetricFamily('network_apic_leaf_capacity_tcam_l3_max',
                                      'ACI Leaf IPv4 EndPoint TCAM capacity available',
                                      labels=['aciLeaf', 'usage', 'layer'])
        g_leaf_cap_tcam_l3_used_total = GaugeMetricFamily('network_apic_leaf_capacity_tcam_l3_used_total',
                                      'ACI Leaf IPv4 EndPoint TCAM capacity total usage',
                                      labels=['aciLeaf', 'usage', 'layer'])
        g_leaf_cap_tcam_l3_used_local = GaugeMetricFamily('network_apic_leaf_capacity_tcam_l3_used_local',
                                      'ACI Leaf Local IPv4 EndPoint TCAM capacity usage',
                                      labels=['aciLeaf', 'usage', 'layer'])
        g_leaf_cap_tcam_l3_used_remote = GaugeMetricFamily('network_apic_leaf_capacity_tcam_l3_used_remote',
                                      'ACI Leaf Remote IPv4 EndPoint TCAM capacity usage',
                                      labels=['aciLeaf', 'usage', 'layer'])
        g_leaf_cap_tcam_l2_max = GaugeMetricFamily('network_apic_leaf_capacity_tcam_l2_max',
                                      'ACI Leaf MAC EndPoint TCAM capacity available',
                                      labels=['aciLeaf', 'usage', 'layer'])
        g_leaf_cap_tcam_l2_used_total = GaugeMetricFamily('network_apic_leaf_capacity_tcam_l2_used_total',
                                      'ACI Leaf MAC EndPoint TCAM capacity total usage',
                                      labels=['aciLeaf', 'usage', 'layer'])
        g_leaf_cap_tcam_l2_used_local = GaugeMetricFamily('network_apic_leaf_capacity_l2_used_local',
                                      'ACI Leaf Local MAC EndPoint TCAM capacity usage',
                                      labels=['aciLeaf', 'usage', 'layer'])
        g_leaf_cap_tcam_l2_used_remote = GaugeMetricFamily('network_apic_leaf_capacity_l2_used_remote',
                                      'ACI Leaf Remote MAC EndPoint TCAM capacity usage',
                                      labels=['aciLeaf', 'usage', 'layer'])

        for leaf in data['imdata']:
            if leaf['eqptcapacityEntity']['children']:
                """Ignore spine switches without children data"""
                leaf_data = leaf['eqptcapacityEntity']['children']
                leaf_dn = leaf['eqptcapacityEntity']['attributes'].split('/')
                leaf_id = leaf_dn[2]
            for data_object in leaf_data:
                if data_object['eqptcapacityL3TotalUsageCap5min']:
                    l3_tcam_cap_max = data_object['eqptcapacityL3TotalUsageCap5min']['attributes']['v4TotalEpCapMax']
                elif data_object['eqptcapacityL3TotalUsage5min']:
                    l3_tcam_cap_used_total = data_object['eqptcapacityL3TotalUsage5min']['attributes']['v4TotalEpAvg']
                elif data_object['eqptcapacityL3Usage5min']:
                    l3_tcam_cap_used_local = data_object['eqptcapacityL3Usage5min']['attributes']['v4LocalEpAvg']
                elif data_object['eqptcapacityL3RemoteUsageCap5min']:
                    l3_tcam_cap_used_remote = data_object['eqptcapacityL3RemoteUsageCap5min']['attributes']['v4RemoteEpCapAvg']
                elif data_object['eqptcapacityL2TotalUsage5min']:
                    l2_tcam_cap_max = data_object['eqptcapacityL2TotalUsage5min']['attributes']['totalEpCapMax']
                    l2_tcam_cap_used_total = data_object['eqptcapacityL2TotalUsage5min']['attributes']['totalEpAvg']
                elif data_object['eqptcapacityL2Usage5min']:
                    l2_tcam_cap_used_local = data_object['eqptcapacityL2Usage5min']['attributes']['localEpAvg']
                elif data_object['eqptcapacityL2RemoteUsage5min']:
                    l2_tcam_cap_used_remote = data_object['eqptcapacityL2RemoteUsage5min']['attributes']['remoteEpAvg']
            g_leaf_cap_tcam_l3_max.add_metric(labels=[leaf_id, 'max', 'l3'],
                                value=l3_tcam_cap_max)
            g_leaf_cap_tcam_l3_used_total.add_metric(labels=[leaf_id, 'total', 'l3'],
                                value=l3_tcam_cap_used_total)
            g_leaf_cap_tcam_l3_used_local.add_metric(labels=[leaf_id, 'local', 'l3'],
                                value=l3_tcam_cap_used_local)
            g_leaf_cap_tcam_l3_used_remote.add_metric(labels=[leaf_id, 'remote', 'l3'],
                                value=l3_tcam_cap_used_remote)
            g_leaf_cap_tcam_l2_max.add_metric(labels=[leaf_id, 'max', 'l2'],
                                value=l2_tcam_cap_max)
            g_leaf_cap_tcam_l2_used_total.add_metric(labels=[leaf_id, 'total', 'l2'],
                                value=l2_tcam_cap_used_total)
            g_leaf_cap_tcam_l2_used_local.add_metric(labels=[leaf_id, 'local', 'l2'],
                                value=l2_tcam_cap_used_local)
            g_leaf_cap_tcam_l2_used_remote.add_metric(labels=[leaf_id, 'remote', 'l2'],
                                value=l2_tcam_cap_used_remote)

        return [g_leaf_cap_tcam_l3_max,
                g_leaf_cap_tcam_l3_used_total,
                g_leaf_cap_tcam_l3_used_local,
                g_leaf_cap_tcam_l3_used_remote,
                g_leaf_cap_tcam_l2_max,
                g_leaf_cap_tcam_l2_used_total,
                g_leaf_cap_tcam_l2_used_local,
                g_leaf_cap_tcam_l2_used_remote]
