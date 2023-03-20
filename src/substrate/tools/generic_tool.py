import subprocess

from docker.types import Mount
from docker import from_env
from docker.types.services import EndpointSpec, ServiceMode


class GenericTool():
  def __init__(self, name, config, data_sources):  # pylint: disable=unused-argument
    # Provide a name for this tool
    self.name = name

    self.config = config
    self.data_sources = data_sources

    # Define the Docker CLI command to create this service on AWS.
    self.service_command = ''
    self.port = 8000
    self.internalPort = self.config.get('internalPort', None)
    self.image = self.config['docker'].get('image', None)
    if self.internalPort is None:
      raise Exception('Option "internalPort" must be defined.')

  # Start a local Docker swarm service
  def start(self):
    # ensure image is defined
    if self.image is None:
      raise Exception('Option "docker.image" must be defined when running substrate locally.')

    mounts = self._setup_mounts()
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

  # Upload files needed to run your service to S3.
  # Upload them to mirror the directory structure you want on EFS.
  def upload_to_s3(self):
    print('Syncing data to S3')

    region = self.config['aws'].get('region', 'us-east-1')
    output = subprocess.check_output('aws s3 ls', shell=True).decode('utf-8')

    if self.config['aws']['bucket'] not in output:
      subprocess.run(
        f'aws s3 mb s3://{self.config["aws"]["bucket"]} --region { region}',
        check=True,
        shell=True
      )

    for data_path in self.data_sources[0]:
      subprocess.run(
        f'aws s3 sync {data_path} s3://{self.config["aws"]["bucket"]}/data',
        check=True,
        shell=True
      )

  # setup te mounts used for the service
  def _setup_mounts(self):
    mounts = []
    data_paths = self.data_sources[0]
    if len(data_paths) > 1:
      for index, data_path in enumerate(data_paths):
        mounts.append(
          Mount(f'/data/{index}', data_path, type='bind', read_only=True)
        )
    else:
      mounts.append(Mount('/data', data_paths[0], type='bind', read_only=True))

    return mounts


