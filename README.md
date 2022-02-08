# Substrate

Substrate is a tool that allows you to automate the process of deploying visualization tools to different computing environments.

### Supported Visualization tools

- [Volume Rendering via Tapestry](https://github.com/seelabutk/tapestry)
- [Flow Visualization via VCI](https://bitbucket.org/seelabutk/vci)
- [Graphing via Braid](https://github.com/seelabutk)

### Supported Environments

Any computing environment capable of running [Docker Swarm](https://docs.docker.com/engine/swarm/) is a valid deployment target.

### Supported Datatypes

VCI currently supports NetCDF data.

### Requirements

- [Python 3.7 or later](https://www.python.org/downloads/).

This tool relies upon Docker Swarm. In order for it to work, the following assumptions are made of each compute node:

- [Docker Engine](https://docs.docker.com/engine/) must be installed. If using automated AWS deployment, VCI will handle this for you.
- The ports needed by Docker Swarm must be open for communication between nodes. Please review the [Docker Swarm docs](https://docs.docker.com/engine/swarm/) for more information.
- You must be able to connect to each node over SSH with a private key available in `~/.ssh`.

### Getting Started (none of this works yet)

To install run

	pip install substrate

then launch a visualization tool via a CLI using

	substrate 'tool_name'

or via Python using

	import substrate
	substrate.launch('tool_name')

Valid tool names:
- tapestry
- vci
- braid

### Configuration

Substrate is configured using substrate.config.yaml. The tool will look for this file starting in your current working directory then look for it in parent folders. You can also provide a path with

	substrate tapestry -c /path/to/substrate.config.yaml

or

	substrate.launch('tool_name', config='path/to/substrate.config.yaml')

### Options

Describe the configuration options here.

### AWS

Describe AWS support here.

### Terraform

If we end up doing it, then describe Terraform support here.
