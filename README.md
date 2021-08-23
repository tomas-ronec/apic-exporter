# APIC Exporter

A Prometheus exporter written in Python3 to retrieve custom metrics from Cisco APICs.

## Adding further metrics

There are two ways to add further metrics. One is extending the [BaseCollector](BaseCollector.py) and the other is extending the [StandardCollector](StandardCollector.py).

When extending from the `BaseCollector` the client has to take care of edge-cases such as the host not answering. The `StandardCollector` takes care of these things and requires solely the logic for creating the Prometheus metrics from query results.

If you want to contribute additional metrics take the [ApicCoopDbCollector](collectors/apiccoobdb.py) as an Example.
Here the metrics are defined as a List of `CustomMetric` objects. Each of these objects contains the name of the metric, the query required to fetch the data from the APIC hosts and a method which processes this data. This method is responsible for creating the Prometheus metric from the fetched data.

## Docker

Build the Docker image locally with `make build`.

And test with `docker run -p 9102:9102 -v ~/Developer/git/apic-exporter/apic-config-sample.yaml:/config.yaml apic-exporter:latest -c /config.yaml`

## Further Readings

- [API configuration guide](https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/2-x/rest_cfg/2_1_x/b_Cisco_APIC_REST_API_Configuration_Guide/b_Cisco_APIC_REST_API_Configuration_Guide_chapter_01.html)

- [APIC Management Information Model Reference](https://developer.cisco.com/site/apic-mim-ref-api/)
