# APIC Exporter

A Prometheus exporter written in Python3 to retrieve custom metrics from Cisco APICs.

## Adding further metrics

There are two ways to add further metrics. One is extending the [BaseCollector](BaseCollector.py) and the other is extending the [Collector](Collector.py).

When extending from the `BaseCollector` the client has to take care of the communication with the different APIC hosts, checking for valid response data etc. The `Collector` takes care of these things and only requires to implement the abstract methods `get_query` (defines the query to be executed against the APIC host) and `get_metrics` (creates the Prometheus metrics from the fetched data).

For most metrics it is sufficient to extend from the [Collector](Collector.py). See [ApicCoopDbCollector](collectors/apiccoopdb.py) as an example.

## Example Config

The exporter is configured by passing a `yaml` of the following structure:

```yaml
exporter:
  log_level: INFO
  prometheus_port: 9102
aci:
  apic_hosts:
  apic_user:
  apic_tenant_name:
collectors:
  - "ApicHealthCollector"
  - "ApicIPsCollector"
  - ...
```

The list of collectors can be used to select the list of collectors to be run. If no collectors are specified, all are run.

Additionally an environment variable `APIC_PASSWORD` is required.

## Docker

Build the Docker image locally with `make build`.

And test with `docker run -p 9102:9102 -v ~/Developer/git/apic-exporter/apic-config-sample.yaml:/config.yaml apic-exporter:latest -c /config.yaml`

## VS Code Dev Container

1. Ensure that your system meets the requirement mentioned in the [Getting Started](https://code.visualstudio.com/docs/devcontainers/containers#_system-requirements) section of the Dev Containers documentation.
2. Clone this repository to your local filesystem
3. Open the repository in VS Code
4. Press `F1`, `CMD+Shift+P` and select __Dev Containers: Reopen in Container__
5. Now you have a running Python Dev Environment.
6. You will need to fill the `apic-config-sample.yaml` and `launch.json` with actual values to be able to debug.

## Further Readings

- [API configuration guide](https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/2-x/rest_cfg/2_1_x/b_Cisco_APIC_REST_API_Configuration_Guide/b_Cisco_APIC_REST_API_Configuration_Guide_chapter_01.html)

- [APIC Management Information Model Reference](https://developer.cisco.com/site/apic-mim-ref-api/)
