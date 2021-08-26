from abc import abstractmethod
import logging
from typing import Dict, List, Tuple
from prometheus_client.core import Summary
from prometheus_client.metrics_core import Metric
from BaseCollector import BaseCollector

LOG = logging.getLogger('apic_exporter.exporter')


class Collector(BaseCollector):
    def __init__(self, name: str, config: Dict):
        super().__init__(config)
        self.__name = name
        self.__request_time = Summary('{name}_processing_seconds'.format(name=self.__name),
                                      'Time spend processing request')

    @abstractmethod
    def get_query(self) -> str:
        pass

    @abstractmethod
    def get_metrics(self, host: str, data: Dict) -> Tuple[List[Metric], int]:
        pass

    def collect(self):
        """Collects the list of metrics defined by the subclass"""
        metric_counter = 0
        with self.__request_time.time():
            LOG.debug('Collecting %s metrics ...', self.__name)
            for host in self.hosts:
                fetched_data = self.query_host(host, self.get_query())
                if fetched_data is None:
                    LOG.warning("Skipping apic host %s did not return anything for %s", host, self.get_query())
                    continue
                metrics, metric_counter = self.get_metrics(host, fetched_data)
                if metrics is None:
                    continue
                for metric in metrics:
                    yield metric
                break  # all hosts produce the same metrics, hence querying one is sufficient
            LOG.info('Collected %s %s metrics', metric_counter, self.__name)
