import subprocess

from . import Tool
from docker.types import Mount
from docker import from_env
from docker.types.services import EndpointSpec, ServiceMode


class GenericTool(Tool):
  def __init__(self, name, config, data_sources):  # pylint: disable=unused-argument
    super().__init__(config, data_sources)
    # Provide a name for this tool
    self.name = name

    self.config = config
    self.tool_config = config[name]
    self.data_sources = data_sources

    # Define the Docker CLI command to create this service on AWS.
    self.service_command = self.tool_config.get('service_command', '')
    self.port = 8000
    self.internalPort = self.tool_config.get('internalPort', None)
    self.image = self.tool_config.get('image', None)
    if self.internalPort is None:
      raise Exception('Option "internalPort" must be defined.')

  # Start a local Docker swarm service
  def start(self):
    # ensure image is defined
    if self.image is None:
      raise Exception('Option "docker.image" must be defined when running substrate locally.')

    mounts = super().start()
    docker = from_env()
    self.port = self.config['docker'].get('port', self.port)
    docker.services.create(
      self.image,
      endpoint_spec=EndpointSpec(ports={self.port: (self.internalPort, 'tcp')}),
      mode=ServiceMode(
        mode='replicated',
        replicas=self.config['docker'].get('replicas', 1)
      ),
      mounts=mounts,
      name=self.name,
      networks=[f'substrate-{self.name}-net'],
      init=True
    )