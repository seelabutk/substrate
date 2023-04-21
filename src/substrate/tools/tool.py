import subprocess

from docker.types import Mount


class Tool():
	def __init__(self, config, data_sources):  # pylint: disable=unused-argument
		# Provide a name for this tool
		self.name = ''

		self.config = config
		self.data_sources = data_sources

		# Define the Docker CLI command to create this service on AWS.
		self.service_command = ''

	# Start a local Docker swarm service
	def start(self):
		mounts = []
		data_paths = self.data_sources[0]
		if len(data_paths) > 1:
			for index, data_path in enumerate(data_paths):
				mounts.append(
					Mount(f'/data/{index}', data_path, type='bind', read_only=True)
				)
		elif len(data_paths) == 1:
			mounts.append(Mount('/data', data_paths[0], type='bind', read_only=True))

		return mounts

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
