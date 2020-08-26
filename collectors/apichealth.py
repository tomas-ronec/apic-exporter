import logging

from prometheus_client.core import GaugeMetricFamily, Summary
import BaseCollector

LOG          = logging.getLogger('apic_exporter.exporter')
REQUEST_TIME = Summary('apic_health_processing_seconds', 'Time spent processing request')

class ApicHealthCollector (BaseCollector.BaseCollector):

    def describe(self):
        yield GaugeMetricFamily('network_apic_accessible', 'APIC controller accessibility')

        yield GaugeMetricFamily('network_apic_cpu_usage_percent', 'APIC CPU utilization')

        yield GaugeMetricFamily('network_apic_max_memory_allocation_bytes', 'APIC maximum memory allocated')

        yield GaugeMetricFamily('network_apic_free_memory_bytes', 'APIC maximum amount of available memory')

    @REQUEST_TIME.time()
    def collect(self):
        LOG.debug('Collecting APIC health metrics ...')

        g_access = GaugeMetricFamily('network_apic_accessible', 'APIC controller accessibility', labels=['apicHost'])

        metric_counter = 0
        for host in self.hosts:
            query = '/api/node/class/topSystem.json?query-target-filter=eq(topSystem.oobMgmtAddr,\"' + host + '\")'
            fetched_data   = self.connection.getRequest(host, query)
            if not self.connection.isDataValid(fetched_data):
                LOG.warning("Skipping apic host %s, %s did not return anything", host, query)
                g_access.add_metric(labels=[host], value=0)
            else:
                g_access.add_metric(labels=[host], value=1)
            metric_counter += 1
        yield  g_access


        g_cpu  = GaugeMetricFamily('network_apic_cpu_usage_percent', 'APIC CPU utilization', labels=['apicHost'])
        g_aloc = GaugeMetricFamily('network_apic_max_memory_allocation_kb', 'APIC maximum memory allocated', labels=['apicHost'])
        g_free = GaugeMetricFamily('network_apic_free_memory_kb', 'APIC maximum amount of available memory', labels=['apicHost'])

        query = '/api/node/class/procEntity.json?'
        for host in self.hosts:
            fetched_data   = self.connection.getRequest(host, query)
            if not self.connection.isDataValid(fetched_data):
                LOG.warning("Skipping apic host %s, %s did not return anything", host, query)
                continue

            g_cpu.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['cpuPct'])
            g_aloc.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['maxMemAlloc'])
            g_free.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['memFree'])
            metric_counter += 3

        yield g_cpu
        yield g_aloc
        yield g_free

        LOG.info('Collected %s APIC health metrics', metric_counter)