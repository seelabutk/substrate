# Visualization Cloud Instance (VCI)

VCI is a tool that allows you to automate the process of deploying popular visualization tools to different computing environments.

### Supported Visualization tools

- [Volume Rendering via Tapestry](https://github.com/seelabutk/tapestry)
- [Flow Visualization via Tannerlol](https://github.com/seelabutk)

### Supported Environments

Any computing environment capable of running [Docker Swarm](https://docs.docker.com/engine/swarm/) is a valid deployment target.

### Supported Datatypes

VCI currently supports NetCDF data.

### Requirements

- [Python 3.7 or later](https://www.python.org/downloads/)
- [Docker Engine](https://docs.docker.com/engine/). This must be installed on all compute nodes. If using automated AWS deployment, VCI will handle this for you.

### Getting Started (none of this works yet)

To install VCI, run

	pip install vci

then launch a visualization tool via a CLI using

	vci 'tool_name'

or via Python using

	import vci
	vci.launch('tool_name')

Valid tool names:
- tapestry
- tannerlol

### Configuration

VCI is configured using vci.config.yaml. The tool will look for this file starting in your current working directory then look for it in parent folders. You can also provide a path with

	vci tapestry -c /path/to/vci.config.yaml

or

	vci.launch('tool_name', config='path/to/vci.config.yaml')

Describe the configuration options here.

Describe AWS support here.

### Terraform (maybe)

Describe Terraform support here (maybe).
