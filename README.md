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
  apic_password:
  apic_tenant_name:
collectors:
  - "ApicHealthCollector"
  - "ApicIPsCollector"
  - ...
```

The list of collectors can be used to select the list of collectors to be run. If no collectors are specified, all are run.

## Docker

Build the Docker image locally with `make build`.

And test with `docker run -p 9102:9102 -v ~/Developer/git/apic-exporter/apic-config-sample.yaml:/config.yaml apic-exporter:latest -c /config.yaml`

## Further Readings

- [API configuration guide](https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/2-x/rest_cfg/2_1_x/b_Cisco_APIC_REST_API_Configuration_Guide/b_Cisco_APIC_REST_API_Configuration_Guide_chapter_01.html)

- [APIC Management Information Model Reference](https://developer.cisco.com/site/apic-mim-ref-api/)
