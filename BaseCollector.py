from abc import ABC, abstractmethod
from modules.Connection import Connection
import logging
from typing import Dict, List

LOG = logging.getLogger('apic_exporter.exporter')


class BaseCollector(ABC):
    def __init__(self, config: Dict):
        self.hosts: List[str] = config['apic_hosts'].split(',')
        self.connection = Connection(self.hosts, config['apic_user'],
                                     config['apic_password'])

    @abstractmethod
    def describe(self):
        pass

    @abstractmethod
    def collect(self):
        pass