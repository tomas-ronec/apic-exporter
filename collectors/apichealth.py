import logging

from prometheus_client.core import GaugeMetricFamily
import BaseCollector

LOG = logging.getLogger('apic_exporter.exporter')

class ApicHealthCollector (BaseCollector.BaseCollector):

    def describe(self):
        yield GaugeMetricFamily('network_apic_accessible', 'APIC accessibility')

        yield GaugeMetricFamily('network_apic_cpu_usage_percent', 'APIC CPU utilization')

        yield GaugeMetricFamily('network_apic_max_memory_allocation_bytes', 'APIC maximum memory allocated')

        yield GaugeMetricFamily('network_apic_free_memory_bytes', 'APIC maximum amount of available memory')

    def collect(self):
        LOG.info('Collecting APIC health metrics ...')

        query = '/api/node/class/procEntity.json?'
        for host in self.hosts:
            fetched_data   = self.connection.getRequest(host, query)
            if not self.connection.isDataValid(fetched_data):
                LOG.error("Skipping apic host %s, %s did not return anything", host, query)
                continue

            # cpu usage
            g = GaugeMetricFamily('network_apic_cpu_usage_percent',
                                  'APIC CPU utilization',
                                  labels=['hostname'])

            g.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['cpuPct'])
            yield g

            # memory allocation
            g = GaugeMetricFamily('network_apic_max_memory_allocation_bytes',
                                  'APIC maximum memory allocated',
                                  labels=['hostname'])

            g.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['maxMemAlloc'])
            yield g

            # free memory
            g = GaugeMetricFamily('network_apic_free_memory_bytes',
                                  'APIC maximum amount of available memory',
                                  labels=['hostname'])

            g.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['memFree'])
            yield g