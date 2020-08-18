SHELL       := /bin/sh
IMAGE       := apic-exporter
VERSION     := latest

### Executables
DOCKER := docker

### Docker Targets

.PHONY: build
build:
	$(DOCKER) build -t $(IMAGE):$(VERSION) --no-cache --rm .
	#$(DOCKER) build -t $(IMAGE):$(VERSION)  .