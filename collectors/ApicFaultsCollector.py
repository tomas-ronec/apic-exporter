from Collector import Collector
import logging
from prometheus_client.core import GaugeMetricFamily
from typing import List, Dict

LOG = logging.getLogger('apic_exporter.exporter')


class ApicFaultsCollector(Collector):

    def __init__(self, config: Dict):
        super().__init__('apic_faults', config)
        self.leaf_ids = {}
        self.gen1_leaves = {}

    def describe(self):
        yield GaugeMetricFamily('network_apic_faults',
                                'APIC faults')

    def get_query(self) -> str:
        return '/api/node/class/faultInst.json?' + \
               'query-target-filter=or(eq(faultInst.lc,"raised"),eq(faultInst.lc,"soaking"))'

    def get_metrics(self, host: str, data: Dict) -> List[GaugeMetricFamily]:
        """Collect and sort APIC Faults by type, severity, domain and acknowledgement"""
        g_apic_faults_severity = GaugeMetricFamily('network_apic_faults_severity',
                                            'APIC faults by severity',
                                            labels=['severity'])
        g_apic_faults_type = GaugeMetricFamily('network_apic_faults_type',
                                            'APIC faults by type',
                                            labels=['type'])
        g_apic_faults_domain = GaugeMetricFamily('network_apic_faults_domain',
                                            'APIC faults by domain',
                                            labels=['domain'])
        g_apic_faults_total = GaugeMetricFamily('network_apic_faults_total',
                                            'APIC faults total',
                                            labels=['total'])
        g_apic_faults_ack = GaugeMetricFamily('network_apic_faults_ack',
                                            'APIC faults acknowledged',
                                            labels=['ack'])

        """faults total"""
        apic_faults_total = data['totalCount']
        g_apic_faults_total.add_metric(labels=['total'],
                                value=apic_faults_total)
        """faults acked"""
        apic_faults_ack = 0
        for fault_object in data['imdata']:
            if fault_object['faultInst']['attributes']['ack'] == 'yes':
                apic_faults_ack =+ 1
        g_apic_faults_ack.add_metric(labels=['ack'],
                                value=apic_faults_ack)
        """faults by severity"""
        apic_faults_sev_critical = 0
        apic_faults_sev_major = 0
        apic_faults_sev_minor = 0
        apic_faults_sev_warning = 0
        apic_faults_sev_info = 0
        apic_faults_sev_cleared = 0
        for fault_object in data['imdata']:
            if fault_object['faultInst']['attributes']['severity'] == 'critical':
                apic_faults_sev_critical =+ 1
            elif fault_object['faultInst']['attributes']['severity'] == 'major':
                apic_faults_sev_major =+ 1
            elif fault_object['faultInst']['attributes']['severity'] == 'minor':
                apic_faults_sev_minor =+ 1
            elif fault_object['faultInst']['attributes']['severity'] == 'warning':
                apic_faults_sev_warning =+ 1
            elif fault_object['faultInst']['attributes']['severity'] == 'info':
                apic_faults_sev_info =+ 1
            elif fault_object['faultInst']['attributes']['severity'] == 'cleared':
                apic_faults_sev_cleared =+ 1
        g_apic_faults_severity.add_metric(labels=['critical'],
                                value=apic_faults_sev_critical)
        g_apic_faults_severity.add_metric(labels=['major'],
                                value=apic_faults_sev_major)
        g_apic_faults_severity.add_metric(labels=['minor'],
                                value=apic_faults_sev_minor)
        g_apic_faults_severity.add_metric(labels=['warning'],
                                value=apic_faults_sev_warning)
        g_apic_faults_severity.add_metric(labels=['info'],
                                value=apic_faults_sev_info)
        g_apic_faults_severity.add_metric(labels=['cleared'],
                                value=apic_faults_sev_cleared)
        """faults by type"""
        apic_faults_type_generic = 0
        apic_faults_type_equipment = 0
        apic_faults_type_configuration = 0
        apic_faults_type_connectivity = 0
        apic_faults_type_environmental = 0
        apic_faults_type_management = 0
        apic_faults_type_network = 0
        apic_faults_type_operational = 0
        for fault_object in data['imdata']:
            if fault_object['faultInst']['attributes']['type'] == 'generic':
                apic_faults_type_generic =+ 1
            elif fault_object['faultInst']['attributes']['type'] == 'equipment':
                apic_faults_type_equipment =+ 1
            elif fault_object['faultInst']['attributes']['type'] == 'configuration':
                apic_faults_type_configuration =+ 1
            elif fault_object['faultInst']['attributes']['type'] == 'connectivity':
                apic_faults_type_connectivity =+ 1
            elif fault_object['faultInst']['attributes']['type'] == 'environmental':
                apic_faults_type_environmental =+ 1
            elif fault_object['faultInst']['attributes']['type'] == 'management':
                apic_faults_type_management =+ 1
            elif fault_object['faultInst']['attributes']['type'] == 'network':
                apic_faults_type_network =+ 1
            elif fault_object['faultInst']['attributes']['type'] == 'operational':
                apic_faults_type_operational =+ 1
        g_apic_faults_type.add_metric(labels=['generic'],
                                value=apic_faults_type_generic)
        g_apic_faults_type.add_metric(labels=['equipment'],
                                value=apic_faults_type_equipment)
        g_apic_faults_type.add_metric(labels=['configuration'],
                                value=apic_faults_type_configuration)
        g_apic_faults_type.add_metric(labels=['connectivity'],
                                value=apic_faults_type_connectivity)
        g_apic_faults_type.add_metric(labels=['environmental'],
                                value=apic_faults_type_environmental)
        g_apic_faults_type.add_metric(labels=['management'],
                                value=apic_faults_type_management)
        g_apic_faults_type.add_metric(labels=['network'],
                                value=apic_faults_type_network)
        g_apic_faults_type.add_metric(labels=['operational'],
                                value=apic_faults_type_operational)
        """faults by domain"""
        apic_faults_domain_infra = 0
        apic_faults_domain_tenant = 0
        apic_faults_domain_access = 0
        apic_faults_domain_external = 0
        apic_faults_domain_framework = 0
        apic_faults_domain_security = 0
        apic_faults_domain_management = 0
        apic_faults_domain_plugin = 0
        for fault_object in data['imdata']:
            if fault_object['faultInst']['attributes']['domain'] == 'infra':
                apic_faults_domain_infra =+ 1
            elif fault_object['faultInst']['attributes']['domain'] == 'tenant':
                apic_faults_domain_tenant =+ 1
            elif fault_object['faultInst']['attributes']['domain'] == 'access':
                apic_faults_domain_access =+ 1
            elif fault_object['faultInst']['attributes']['domain'] == 'external':
                apic_faults_domain_external =+ 1
            elif fault_object['faultInst']['attributes']['domain'] == 'framework':
                apic_faults_domain_framework =+ 1
            elif fault_object['faultInst']['attributes']['domain'] == 'security':
                apic_faults_domain_security =+ 1
            elif fault_object['faultInst']['attributes']['domain'] == 'management':
                apic_faults_domain_management =+ 1
            elif fault_object['faultInst']['attributes']['domain'] == 'plugin':
                apic_faults_domain_plugin =+ 1
        g_apic_faults_domain.add_metric(labels=['infra'],
                                value=apic_faults_domain_infra)
        g_apic_faults_domain.add_metric(labels=['tenant'],
                                value=apic_faults_domain_tenant)
        g_apic_faults_domain.add_metric(labels=['access'],
                                value=apic_faults_domain_access)
        g_apic_faults_domain.add_metric(labels=['external'],
                                value=apic_faults_domain_external)
        g_apic_faults_domain.add_metric(labels=['framework'],
                                value=apic_faults_domain_framework)
        g_apic_faults_domain.add_metric(labels=['security'],
                                value=apic_faults_domain_security)
        g_apic_faults_domain.add_metric(labels=['management'],
                                value=apic_faults_domain_management)
        g_apic_faults_domain.add_metric(labels=['plugin'],
                                value=apic_faults_domain_plugin)
        return [g_apic_faults_severity,g_apic_faults_type,g_apic_faults_domain,g_apic_faults_total,g_apic_faults_ack]
