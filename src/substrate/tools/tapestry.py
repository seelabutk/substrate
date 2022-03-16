from copy import deepcopy
from glob import glob
import json
import os
import subprocess

from docker import from_env
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class Tapestry(Tool):
	def __init__(self, config, data_sources):
		super().__init__(config, data_sources)

		self.name = 'tapestry'
		self.config = config

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
		docker = from_env()

		mounts = [f'{self.app_path}:/app:ro', f'{self.config_path}:/config:ro']
		data_paths = self.data_sources[0]
		if len(data_paths) > 1:
			for index, data_path in enumerate(data_paths):
				mounts.append(f'{data_path}:/data/{index}:ro')
		else:
			mounts.append(f'{data_paths[0]}:/data:ro')

		port = self.config['cluster'].get('port', 8080)
		docker.services.create(
			'evilkermit/substrate_tapestry:latest',
			'./server',
			args=['/config', '9010', '/app'],
			endpoint_spec=EndpointSpec(ports={port: (9010, 'tcp')}),
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

		for data_path in self.data_sources[0]:
			subprocess.run([
				'aws',
				's3',
				'sync',
				data_path,
				f's3://{self.config["aws"]["bucket"]}/data'
			], check=True)
