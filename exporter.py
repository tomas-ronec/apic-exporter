import yaml
import logging
import os
import sys
import time
import click

from prometheus_client.core import REGISTRY
from prometheus_client import start_http_server

from collectors import apicspineport, apichealth, apicinterfaces, apicprocesses, apicips, apiccoopdb, apiceqpt, apicmcpfault
LOG = logging.getLogger('apic_exporter.exporter')


def run_prometheus_server(port, apic_config):
    start_http_server(int(port))
    REGISTRY.register(apichealth.ApicHealthCollector(apic_config))
    REGISTRY.register(apicinterfaces.ApicInterfacesCollector(apic_config))
    REGISTRY.register(apicprocesses.ApicProcessesCollector(apic_config))
    REGISTRY.register(apicips.ApicIPsCollector(apic_config))
    REGISTRY.register(apiccoopdb.ApicCoopDbCollector(apic_config))
    REGISTRY.register(apiceqpt.ApicEquipmentCollector(apic_config))
    REGISTRY.register(apicmcpfault.ApicMCPCollector(apic_config))
    REGISTRY.register(apicspineport.ApicSpinePortsCollector(apic_config))
    while True:
        time.sleep(1)


def get_config(config_file):
    if os.path.exists(config_file):
        try:
            with open(config_file) as f:
                config = yaml.load(f, Loader=yaml.Loader)
        except IOError as e:
            LOG.error("Couldn't open configuration file: " + str(e))
        return config
    else:
        LOG.error("Config file doesn't exist: " + config_file)
        exit(0)


@click.command()
@click.option("-p",
              "--port",
              metavar="<port>",
              default=9102,
              help="specify exporter serving port")
@click.option("-c", "--config", metavar="<config>", help="path to rest config")
@click.version_option()
@click.help_option()
def main(port, config):

    if not config:
        raise click.ClickException("Missing APIC config yaml --config")

    config_obj = get_config(config)
    exporter_config = config_obj['exporter']
    apic_config = config_obj['aci']

    level = logging.getLevelName("INFO")
    if exporter_config['log_level']:
        level = logging.getLevelName(exporter_config['log_level'].upper())

    format = '[%(asctime)s] [%(levelname)s] %(message)s'
    logging.basicConfig(stream=sys.stdout, format=format, level=level)

    LOG.info("Starting Apic Exporter on port={} config={}".format(port, config))
    LOG.info("APIC Exporter connects to APIC hosts: %s", apic_config['apic_hosts'])

    run_prometheus_server(port, apic_config)


if __name__ == '__main__':
    main()
