import re, logging

from prometheus_client.core import GaugeMetricFamily, Summary
import BaseCollector

LOG = logging.getLogger('apic_exporter.exporter')
REQUEST_TIME = Summary('apic_processes_processing_seconds', 'Time spent processing request')

class ApicProcessesCollector (BaseCollector.BaseCollector):

    def describe(self):
        yield GaugeMetricFamily('network_apic_process_memory_used_min_kb', 'Minimum memory used by process')

        yield GaugeMetricFamily('network_apic_process_memory_used_max_kb', 'Maximum memory used by process')

        yield GaugeMetricFamily('network_apic_process_memory_used_avg_kb', 'Average memory used by process')

    @REQUEST_TIME.time()
    def collect(self):
        LOG.info('Collecting APIC health metrics ...')

        g_mem_min = GaugeMetricFamily('network_apic_process_memory_used_min_kb',
                                      'Minimum memory used by process',
                                      labels=['apicHost', 'procName', 'nodeId', 'nodeRole'])

        g_mem_max = GaugeMetricFamily('network_apic_process_memory_used_max_kb',
                                      'Maximum memory used by process',
                                      labels=['apicHost', 'procName', 'nodeId', 'nodeRole'])

        g_mem_avg = GaugeMetricFamily('network_apic_process_memory_used_avg_kb',
                                      'Average memory used by process',
                                      labels=['apicHost', 'procName', 'nodeId', 'nodeRole'])

        query = '/api/node/class/fabricNode.json?'
        for host in self.hosts:
            fetched_data   = self.connection.getRequest(host, query)
            if not self.connection.isDataValid(fetched_data):
                LOG.error("Skipping apic host %s, %s did not return anything", host, query)
                continue

            # fetch nfm process id from each node
            for node in fetched_data['imdata']:
                node_dn   = node['fabricNode']['attributes']['dn']
                node_role = node['fabricNode']['attributes']['role']
                LOG.debug("Fetching process data for node %s %s", node_dn, node_role)

                proc_query = '/api/node/class/' + node_dn + '/procProc.json?query-target-filter=eq(procProc.name,"nfm")'
                proc_data  = self.connection.getRequest(host, proc_query)
                if not self.connection.isDataValid(proc_data):
                    LOG.error("Apic host %s node %s has no nfm process", host, node_dn)
                    continue

                # fetch nfm process memory consumption per node
                if int(proc_data['totalCount']) > 0:
                    proc_dn   = proc_data['imdata'][0]['procProc']['attributes']['dn']
                    proc_name = proc_data['imdata'][0]['procProc']['attributes']['name']
                    mem_query = '/api/node/mo/' + proc_dn + '/HDprocProcMem5min-0.json'
                    mem_data  = self.connection.getRequest(host, mem_query)
                    if not self.connection.isDataValid(mem_data):
                        LOG.error("Apic host %s node %s process %s has no memory data", host, node_dn, proc_dn)
                        continue

                    if int(mem_data['totalCount']) > 0:
                        node_id = self._parseNodeIdInProcDN(proc_dn)

                        LOG.debug("procName: %s, nodeId: %s, role: %s, MemUsedMin: %s, MemUsedMax: %s, MemUsedAvg: %s",
                                  proc_name, node_id, node_role,
                                  mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedMin'],
                                  mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedMax'],
                                  mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedAvg'])

                        # Min memory used
                        g_mem_min.add_metric(labels=[host, proc_name, node_id, node_role], value=mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedMin'])

                        # Max memory used
                        g_mem_max.add_metric(labels=[host, proc_name, node_id, node_role], value=mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedMax'])

                        # Avg memory used
                        g_mem_avg.add_metric(labels=[host, proc_name, node_id, node_role], value=mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedAvg'])

        yield g_mem_min
        yield g_mem_max
        yield g_mem_avg

    def _parseNodeIdInProcDN(self, procDn):
        nodeId = ''
        matchObj = re.match(u".+node-([0-9]*).+", procDn)
        if matchObj:
            nodeId = matchObj.group(1)
        return nodeId