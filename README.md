# Substrate

Substrate is a tool that allows you to automate the process of deploying visualization tools to different computing environments.

### Supported Visualization tools

- NetCDF Slicer
- [OSPRay Studio](https://github.com/ospray/ospray_studio)
- [Volume Rendering via Tapestry](https://github.com/seelabutk/tapestry)
- [Flow Visualization via Braid](https://bitbucket.org/seelabutk/vci)

### Supported Environments

Any computing environment capable of running [Docker Swarm](https://docs.docker.com/engine/swarm/) is a valid deployment target.

### Requirements

- [Python 3.7 or later](https://www.python.org/downloads/).

This tool relies upon Docker Swarm. In order for it to work, the following assumptions are made of each compute node (for AWS deployments, these requirements are handled automatically):

- [Docker Engine](https://docs.docker.com/engine/) must be installed.
- The ports needed by Docker Swarm must be open for communication between nodes. Please review the [Docker Swarm docs](https://docs.docker.com/engine/swarm/) for more information.
- You must be able to connect to each node over SSH with a private key available in `~/.ssh`.

### Getting Started

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
- hello_world (this will just host the provided data sources as static files)
- nc_slicer
- ospray_studio
- tapestry
- braid

### Configuration

Substrate is configured using `substrate.config.yaml`. The tool will look for this file starting in your current working directory then look for it in parent folders. You can also provide a path with

	substrate tapestry start -f /path/to/substrate.config.yaml

or

	stack = Substrate('tool_name', {}, path='path/to/substrate.config.yaml')

You may also specify the config directly via JSON/a dictionary with

	substrate tapestry start -c "{ config here... }"

or

	stack = Substrate('tool_name', config)

The options for the configuration file can be found [here](api/substrate.config.yaml).

Each tool has static files that are needed to run it. Defaults are provided, but if needed or desired they can be modified. Here are links to get the default files for [Tapestry](src/substrate/tapestry) and [Braid](src/substrate/vci).

For more information on configuring each tool, please refer to each tools documentation:
- NetCDF Slicer: coming soon
- [OSPRay Studio](https://github.com/ospray/ospray_studio)
- [Tapestry](https://github.com/seelabutk/tapestry)
- [Braid](https://bitbucket.org/seelabutk/vci)

### Development Environment

To setup the dev environment, please install [Pipenv](https://pipenv-fork.readthedocs.io/en/latest/index.html). Once installed, run the following commands to set up the development environment:

	pipenv --python /path/to/your/python3.10
	pipenv sync -d
	pipenv shell

### Uploading to PyPI

To upload to prepare a new release, run the following commands:

	python -m build
	python -m twine upload dist/*
