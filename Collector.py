from abc import abstractmethod
import logging
from typing import Callable, Dict, List, Tuple
from dataclasses import dataclass
from prometheus_client.core import Summary
from prometheus_client.metrics_core import Metric
from BaseCollector import BaseCollector

LOG = logging.getLogger('apic_exporter.exporter')


@dataclass
class CustomMetric:
    name: str
    query: str
    process_data: Callable[[str, Dict], Tuple[Metric, int]]


class Collector(BaseCollector):
    def __init__(self, name: str, config: Dict):
        super().__init__(config)
        self.__metric_counter = 0
        self.__name = name
        self.__request_time = Summary('{name}_processing_seconds'.format(name=self.__name),
                                      'Time spend processing request')

    @abstractmethod
    def get_metric_definitions(self) -> List[CustomMetric]:
        """Returns the list of metrics to be collected by the collector"""
        pass

    def collect(self):
        """Collects the list of metrics defined by the subclass"""
        self.__metric_counter = 0
        metrics = self.get_metric_definitions()
        with self.__request_time.time():
            LOG.debug('Collecting %s metrics ...', self.__name)
            for metric in metrics:
                LOG.debug('Collecting metric %s', metric.name)
                for host in self.hosts:
                    fetched_data = self.query_host(host, metric.query)
                    if fetched_data is None:
                        LOG.warning("Skipping apic host %s did not return anything for %s", host, metric.name)
                        continue
                    metric_family, count = metric.process_data(host, fetched_data)
                    if metric_family is None:
                        continue
                    self.__metric_counter += count
                    yield metric_family
                    break  # all hosts produce the same metrics, hence querying one is sufficient
            LOG.info('Collected %s %s metrics', self.__metric_counter, self.__name)
