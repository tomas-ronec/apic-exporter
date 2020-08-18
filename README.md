# apic-exporter
prometheus exporter written in python3 to get custom apic metrics

Further information about the Cisco APIC REST API can be found in the [API configuration guide](https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/2-x/rest_cfg/2_1_x/b_Cisco_APIC_REST_API_Configuration_Guide/b_Cisco_APIC_REST_API_Configuration_Guide_chapter_01.html).

## Docker

Build the Docker image locally with `make build`. 
 
And test with `docker run -p 9102:9102 -v ~/Developer/git/apic-exporter/apic-config-sample.yaml:/config.yaml apic-exporter:latest -c /config.yaml`