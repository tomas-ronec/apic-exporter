import logging
import re
from collections import namedtuple
from typing import Dict, List

import BaseCollector
from prometheus_client.core import GaugeMetricFamily, Summary

LOG = logging.getLogger('apic_exporter.exporter')
TIMEOUT = 5
REQUEST_TIME = Summary('apic_equipment_processing_seconds',
                       'Time spent processing request')


class ApicEquipmentCollector(BaseCollector.BaseCollector):

    def __init__(self, config: Dict):
        super().__init__(config)
        self.__metric_counter = 0

    def describe(self):
        yield GaugeMetricFamily('network_apic_flash_readwrite',
                                'APIC flash is read and writeable')

    def collect_flash(self) -> GaugeMetricFamily:
        """Collect read-write status of flash equipment"""

        g_flash_rw = GaugeMetricFamily('network_apic_flash_readwrite',
                                       'APIC flash is read and writeable',
                                       labels=['apicHost', 'node', 'type', 'vendor', 'model'])

        eqpt_template = namedtuple("apic_equipment", ['type', 'vendor', 'model', 'nodeId', 'acc'])

        for host in self.hosts:
            query = '/api/node/class/eqptFlash.json' + \
                    '?rsp-subtree=full&query-target-filter=wcard(eqptFlash.model,\"Micron_M500IT\")'
            fetched_data = self.connection.getRequest(host, query, TIMEOUT)
            if not self.connection.isDataValid(fetched_data):
                LOG.warning(
                    "Skipping apic host %s, %s did not return anything", host,
                    query)

            # get a list of all flash devices NOT in read-write mode
            flashes = [eqpt_template(type=d['eqptFlash']['attributes']['type'],
                                     vendor=d['eqptFlash']['attributes']['vendor'],
                                     model=d['eqptFlash']['attributes']['model'],
                                     nodeId=self._parseNodeId(d['eqptFlash']['attributes']['dn']),
                                     acc=d['eqptFlash']['attributes']['acc']
                                     )
                       for d in fetched_data['imdata'] if d['eqptFlash']['attributes']['model'].startswith('Micron_M500IT')
                       ]

            for flash in flashes:
                if flash.acc == 'read-write':
                    g_flash_rw.add_metric(labels=[host, flash.nodeId, flash.type, flash.vendor, flash.model], value=1)
                else:
                    g_flash_rw.add_metric(labels=[host, flash.nodeId, flash.type, flash.vendor, flash.model], value=0)
                self.__metric_counter += 1

            break  # Each host produces the same metrics

        return g_flash_rw

    @REQUEST_TIME.time()
    def collect(self):
        LOG.debug('Collecting APIC quipment metrics ...')

        self.reset_unavailable_hosts()

        self.__metric_counter = 0

        metrics: List[GaugeMetricFamily] = []

        metrics.append(self.collect_flash())

        for metric in metrics:
            yield metric

        LOG.info('Collected %s APIC equipment metrics', self.__metric_counter)

    def _parseNodeId(self, dn):
        matchObj = re.match(u".+node-([0-9]*).+", dn)
        return matchObj.group(1) if matchObj is not None else ''
