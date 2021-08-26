import logging
import re
from collections import namedtuple
from typing import Dict, List, Tuple

from Collector import Collector
from prometheus_client.core import Metric, GaugeMetricFamily

LOG = logging.getLogger('apic_exporter.exporter')


class ApicEquipmentCollector(Collector):

    def __init__(self, config: Dict):
        super().__init__('apic_equipment', config)

    def describe(self):
        yield GaugeMetricFamily('network_apic_flash_readwrite',
                                'APIC flash is read and writeable')

    def get_query(self) -> str:
        query = '/api/node/class/eqptFlash.json' + \
                '?rsp-subtree=full&query-target-filter=wcard(eqptFlash.model,\"Micron_M500IT\")'
        return query

    def get_metrics(self, host: str, data: Dict) -> Tuple[List[Metric], int]:
        """Collect read-write status of flash equipment"""

        g_flash_rw = GaugeMetricFamily('network_apic_flash_readwrite',
                                       'APIC flash is read and writeable',
                                       labels=['apicHost', 'node', 'type', 'vendor', 'model'])
        metric_counter = 0

        eqpt_template = namedtuple("apic_equipment", ['type', 'vendor', 'model', 'nodeId', 'acc'])

        # get a list of all flash devices NOT in read-write mode
        flashes = [eqpt_template(type=d['eqptFlash']['attributes']['type'],
                                 vendor=d['eqptFlash']['attributes']['vendor'],
                                 model=d['eqptFlash']['attributes']['model'],
                                 nodeId=self._parseNodeId(d['eqptFlash']['attributes']['dn']),
                                 acc=d['eqptFlash']['attributes']['acc']
                                 )
                   for d in data['imdata'] if d['eqptFlash']['attributes']['model'].startswith('Micron_M500IT')
                   ]

        for flash in flashes:
            if flash.acc == 'read-write':
                g_flash_rw.add_metric(labels=[host, flash.nodeId, flash.type, flash.vendor, flash.model], value=1)
            else:
                g_flash_rw.add_metric(labels=[host, flash.nodeId, flash.type, flash.vendor, flash.model], value=0)
            metric_counter += 1

        return [g_flash_rw], metric_counter

    def _parseNodeId(self, dn):
        matchObj = re.match(u".+node-([0-9]*).+", dn)
        return matchObj.group(1) if matchObj is not None else ''
