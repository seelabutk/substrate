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
		else:
			mounts.append(Mount('/data', data_paths[0], type='bind', read_only=True))

		return mounts

	# Upload files needed to run your service to S3.
	# Upload them to mirror the directory structure you want on EFS.
	def upload_to_s3(self):
		for data_path in self.data_sources[0]:
			subprocess.run([
				'aws',
				's3',
				'sync',
				data_path,
				f's3://{self.config["aws"]["bucket"]}/data'
			], check=True)
