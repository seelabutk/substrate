from copy import deepcopy
from glob import glob
import json
import os
import subprocess

from docker import from_env
from docker.types import Mount
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class Tapestry(Tool):  # pylint: disable=too-many-instance-attributes
	def __init__(self, config, data_sources):
		super().__init__(config, data_sources)

		self.name = 'tapestry'
		self.config = config
		self.port = 8000

		self.service_command = (
			'docker service create '
			'--env APP_DIR=/app '
			'--name tapestry '
			'--publish 80:9010/tcp '
			f'--replicas {self.config.get("aws", {}).get("replicas", 1)} '
			'--mount type=bind,src=/mnt/efs/app,dst=/app '
			'--mount type=bind,src=/mnt/efs/config,dst=/config '
			'--mount type=bind,src=/mnt/efs/data,dst=/data '
			'evilkermit/substrate_tapestry:latest '
			'./server /config 9010 /app'
		)

		fallback_dir = os.path.join(os.path.dirname(__file__), 'tapestry')

		self.tapestry_path = self.config['tapestry'].get('directory', fallback_dir)
		self.app_path = os.path.join(self.tapestry_path, 'app')
		self.config_path = os.path.join(self.tapestry_path, 'config')
		self.data_sources = data_sources

		self.set_config()

	def set_config(self):
		config_file = glob(os.path.join(self.config_path, '*.json'))[0]
		with open(config_file, 'r', encoding='utf8') as _file:
			tapestry_config = json.load(_file)
			new_config = deepcopy(tapestry_config)

			filename = self.config['tapestry']['filename']

			# Set dataset-specific Tapestry configuration
			new_config['filename'] = f'/data/{filename}'
			new_config['dimensions'] = self.config['tapestry']['dimensions']
			new_config['cameraPosition'] = [
				0,
				0,
				tapestry_config['dimensions'][-1] * 2
			]

		# Save the config so it can be changed by the user
		if new_config != tapestry_config:
			with open(config_file, 'w', encoding='utf8') as _file:
				json.dump(new_config, _file)

	def start(self):
		mounts = super().start()
		docker = from_env()

		mounts.append(Mount('/app', self.app_path, type='bind', read_only=True))
		mounts.append(
			Mount('/config', self.config_path, type='bind', read_only=True)
		)

		self.port = self.config['cluster'].get('port', self.port)
		docker.services.create(
			'evilkermit/substrate_tapestry:latest',
			'./server',
			args=['/config', '9010', '/app'],
			endpoint_spec=EndpointSpec(ports={self.port: (9010, 'tcp')}),
			env=['APP_DIR=/app'],
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['cluster'].get('replicas', 1)
			),
			mounts=mounts,
			name='tapestry',
			networks=['substrate-tapestry-net']
		)

	def upload_to_s3(self):
		super().upload_to_s3()

		subprocess.run([
			'aws',
			's3',
			'sync',
			self.app_path,
			f's3://{self.config["aws"]["bucket"]}/app'
		], check=True)

		subprocess.run([
			'aws',
			's3',
			'sync',
			self.config_path,
			f's3://{self.config["aws"]["bucket"]}/config'
		], check=True)
