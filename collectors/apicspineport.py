import logging
import BaseCollector
from prometheus_client.core import GaugeMetricFamily, Summary
from typing import Dict

LOG = logging.getLogger('apic_exporter.exporter')
REQUEST_TIME = Summary('apic_spine_ports_counter',
                       'Time spent processing request')


class ApicSpinePortsCollector(BaseCollector.BaseCollector):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.__metric_counter = 0

    def describe(self):
        yield GaugeMetricFamily('network_apic_free_port_count',
                                'Total available free ports')

        yield GaugeMetricFamily('network_apic_used_port_count',
                                'Total in-use ports')

        yield GaugeMetricFamily('network_apic_down_port_count',
                                'In-use but down ports')

    @REQUEST_TIME.time()
    def collect(self):
        LOG.debug('Collecting APIC Spine ports metrics ...')

        g_free_port = GaugeMetricFamily(
            'network_apic_free_port_count',
            'Total available free ports',
            labels=['apicHost', 'Spine_id', 'pod_id'])

        g_used_port = GaugeMetricFamily(
            'network_apic_used_port_count',
            'Total in-use ports',
            labels=['apicHost', 'Spine_id', 'pod_id'])

        g_down_port = GaugeMetricFamily(
            'network_apic_down_port_count',
            'In-use but down ports',
            labels=['apicHost', 'Spine_id', 'pod_id'])

        query_url = '/api/node/class/fabricNode.json?' + \
                    '&query-target-filter=eq(fabricNode.role,"spine")&order-by=fabricNode.id|asc'
        for host in self.hosts:
            output = self.query_host(host, query_url)
            if output is None:
                continue
            count = output['totalCount']
            spine_dn_list = []
            for x in range(0, int(count)):
                dn = str(output['imdata'][x]['fabricNode']['attributes']['dn'])
                spine_dn_list.append(str(dn))

            # fetch physcal port from each spine
            for dn in spine_dn_list:
                query_url = '/api/node/mo/' + dn + '/sys.json?rsp-subtree=full&rsp-subtree-class=ethpmPhysIf'
                free_port = []
                used_port = []
                down_port = []
                
                output = self.query_host(host, query_url)
                if output is None:
                    continue
                    
                for x in output['imdata']:
                    pod_id = x['topSystem']['attributes']['podId']
                    spine_id = x['topSystem']['attributes']['id']
                    for port_dict in x['topSystem']['children']:
                        if (port_dict['l1PhysIf']['attributes']['adminSt'] == 'up' and port_dict['l1PhysIf']['children'][0]['ethpmPhysIf']['attributes']['operSt'] == 'down'):
                            port_number = port_dict['l1PhysIf']['attributes']['id']
                            free_port.append(str(port_number))

                        elif (port_dict['l1PhysIf']['attributes']['adminSt'] == 'up' and port_dict['l1PhysIf']['children'][0]['ethpmPhysIf']['attributes']['operSt'] == 'up'):
                            port_number = port_dict['l1PhysIf']['attributes']['id']
                            used_port.append(str(port_number))

                        elif port_dict['l1PhysIf']['attributes']['adminSt'] == 'down':
                            port_number = port_dict['l1PhysIf']['attributes']['id']
                            down_port.append(str(port_number))

                free_port_count = len(free_port)
                used_port_count = len(used_port)
                down_port_count = len(down_port)
                # Free Ports
                g_free_port.add_metric(
                    labels=[host, spine_id, pod_id],
                    value=free_port_count)

                # Used Ports
                g_used_port.add_metric(
                    labels=[host, spine_id, pod_id],
                    value=used_port_count)

                # Down ports
                g_down_port.add_metric(
                    labels=[host, spine_id, pod_id],
                    value=down_port_count)

                self.__metric_counter += 1

            break  # Each host produces the same metrics.

        yield g_free_port
        yield g_used_port
        yield g_down_port

        LOG.info('Collected %s APIC Spine ports metrics', self.__metric_counter)
