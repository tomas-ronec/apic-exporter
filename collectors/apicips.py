import logging, re

from prometheus_client.core import CounterMetricFamily, Summary
import BaseCollector

LOG          = logging.getLogger('apic_exporter.exporter')
REQUEST_TIME = Summary('apic_ips_processing_seconds', 'Time spent processing request')

class ApicIPsCollector (BaseCollector.BaseCollector):

    def describe(self):
        yield CounterMetricFamily('network_apic_duplicate_ip_counter', 'Counter for duplicate IPs')

    @REQUEST_TIME.time()
    def collect(self):
        LOG.info('Collecting APIC IP metrics ...')

        g_dip= CounterMetricFamily('network_apic_duplicate_ip_counter',
                                   'Counter for duplicate IPs',
                                    labels=['apicHost', 'ip', 'mac', 'nodeId', 'tenant'])

        metric_counter = 0
        query = '/api/node/class/fvIp.json?rsp-subtree=full&rsp-subtree-class=fvReportingNode&query-target-filter=and(ne(fvIp.debugMACMessage,""))'
        for host in self.hosts:
            fetched_data   = self.connection.getRequest(host, query)
            if not self.connection.isDataValid(fetched_data):
                LOG.warning("Skipping apic host %s, %s did not return anything", host, query)
                continue

            for ip in fetched_data['imdata']:
                addr   = ip['fvIp']['attributes']['addr']
                dn     = ip['fvIp']['attributes']['dn']
                mac    = re.search(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", dn).group()
                tenant = re.match(r"uni\/tn-(.+)\/ap.+", dn)[1]

                child_nodes = []
                if 'children' in ip['fvIp']:
                    for child in ip['fvIp']['children']:
                        node_id = child['fvReportingNode']['attributes']['id']
                        child_nodes.append(str(node_id))

                _nodeIds = 'None'
                if child_nodes:
                    _nodeIds = '+'.join(child_nodes)

                LOG.debug("host: %s, ip: %s, mac: %s, nodes: %s", host, addr, mac, _nodeIds)
                metric_counter += 1

                g_dip.add_metric(labels=[host, addr, mac, _nodeIds, tenant], value=1)

        yield g_dip

        LOG.info('Collected %s APIC IP metrics', metric_counter)