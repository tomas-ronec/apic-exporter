import yaml
import logging
import os
import sys
import time
import click

from prometheus_client.core import REGISTRY
from prometheus_client import start_http_server

from collectors import apichealth, apicinterfaces, apicprocesses,apicips

def run_prometheus_server(port, apic_config):
    start_http_server(int(port))
    REGISTRY.register(apichealth.ApicHealthCollector(apic_config))
    REGISTRY.register(apicinterfaces.ApicInterfacesCollector(apic_config))
    REGISTRY.register(apicprocesses.ApicProcessesCollector(apic_config))
    REGISTRY.register(apicips.ApicIPsCollector(apic_config))
    while True:
        time.sleep(1)


def get_config(config_file):
    if os.path.exists(config_file):
        try:
            with open(config_file) as f:
                config = yaml.load(f, Loader=yaml.Loader)
        except IOError as e:
            logging.error("Couldn't open configuration file: " + str(e))
        return config
    else:
        logging.error("Config file doesn't exist: " + config_file)
        exit(0)

@click.command()
@click.option("-p", "--port", metavar="<port>", default=9102, help="specify exporter serving port")
@click.option("-c", "--config", metavar="<config>", help="path to rest config")
@click.version_option()
@click.help_option()
def main(port, config):

    if not config:
        raise click.ClickException("Missing APIC config yaml --config")

    config_obj      = get_config(config)
    exporter_config = config_obj['exporter']
    apic_config     = config_obj['aci']

    log = logging.getLogger(__name__)
    if exporter_config['log_level']:
        log.setLevel(logging.getLevelName(
            exporter_config['log_level'].upper()))
    else:
        log.setLevel(logging.getLevelName("INFO"))

    format = '[%(asctime)s] [%(levelname)s] %(message)s'
    logging.basicConfig(stream=sys.stdout, format=format)

    log.info("Starting Apic Exporter on port={} config={}".format(
        port,
        config
    ))

    run_prometheus_server(port, apic_config)

if __name__ == '__main__':
    main()