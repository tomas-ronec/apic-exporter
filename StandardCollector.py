import logging
from typing import Callable, Dict, List
from dataclasses import dataclass
from prometheus_client.core import Summary
from prometheus_client.metrics_core import Metric
import BaseCollector

LOG = logging.getLogger('apic_exporter.exporter')


@dataclass
class CustomMetric:
    name: str
    query: str
    process_data: Callable[[str, Dict], List[Metric]]


class StandardCollector(BaseCollector.BaseCollector):
    def __init__(self, name: str, config: Dict, metrics: List[CustomMetric]):
        super().__init__(config)
        self.__metrics = metrics
        self.__metric_counter = 0
        self.__name = name
        self.__request_time = Summary('{name}_processing_seconds'.format(name=self.__name),
                                      'Time spend processing request')

    def collect(self):
        self.__metric_counter = 0
        with self.__request_time.time():
            LOG.debug('Collecting %s metrics ...', self.__name)
            for metric in self.__metrics:
                for host in self.hosts:
                    fetched_data = self.query_host(host, metric.query)
                    if fetched_data is None:
                        LOG.warning("Skipping apic host %s, %s did not return anything", host, self.__query)
                        continue
                    metric_family = metric.process_data(host, fetched_data)
                    if metric_family is None:
                        continue
                    self.__metric_counter += len(metric_family.samples)
                    yield metric_family
                    break  # all hosts produce the same metrics, hence querying one is sufficient
            LOG.info('Collected %s %s metrics', self.__metric_counter, self.__name)
