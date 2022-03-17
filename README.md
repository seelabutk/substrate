# Substrate

Substrate is a tool that allows you to automate the process of deploying visualization tools to different computing environments.

### Supported Visualization tools

- [Volume Rendering via Tapestry](https://github.com/seelabutk/tapestry)
- [Flow Visualization via VCI](https://bitbucket.org/seelabutk/vci)

### Supported Environments

Any computing environment capable of running [Docker Swarm](https://docs.docker.com/engine/swarm/) is a valid deployment target.

### Requirements

- [Python 3.7 or later](https://www.python.org/downloads/).

This tool relies upon Docker Swarm. In order for it to work, the following assumptions are made of each compute node (for AWS deployments, these requirements are handled automatically):

- [Docker Engine](https://docs.docker.com/engine/) must be installed.
- The ports needed by Docker Swarm must be open for communication between nodes. Please review the [Docker Swarm docs](https://docs.docker.com/engine/swarm/) for more information.
- You must be able to connect to each node over SSH with a private key available in `~/.ssh`.

### Getting Started (none of this works yet)

To install run

	pip install seelabutk-substrate

then launch a visualization tool via a CLI using

	substrate 'tool_name' start
	substrate 'tool_name' stop

or via Python using

	from substrate import Substrate

	stack = Substrate('tool_name')
	stack.start()
	stack.stop()

Valid tool names:
- tapestry
- vci

### Configuration

Substrate is configured using `substrate.config.yaml`. The tool will look for this file starting in your current working directory then look for it in parent folders. You can also provide a path with

	substrate tapestry start -c /path/to/substrate.config.yaml

or

	stack = Substrate('tool_name', path='path/to/substrate.config.yaml')

The options for the configuration file can be found [here](api/substrate.config.yaml).

Each tool has static files that are needed to run it. Defaults are provided, but if needed or desired they can be modified. Here are links to get the default files for [Tapestry](src/substrate/tapestry) and [VCI](src/substrate/vci).

For more information on configuring each tool, please refer to each tools documentation:
- [Tapestry](https://github.com/seelabutk/tapestry)
- [VCI](https://bitbucket.org/seelabutk/vci)
