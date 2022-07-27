import os
import subprocess
from time import sleep

from aws_cdk import App, RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_efs as efs
from aws_cdk import aws_iam as iam
import requests


class AWSStack():
	def __init__(self, path, config, tool):
		self.path = path
		self.config = config
		self.tool = tool

		app = App()
		_AWSStack(
			app,
			f'substrate-stack-{self.tool.name}',
			tool,
			config,
			self.tool.data_sources[1]
		)
		app.synth()

	def start(self):
		subprocess.run(
			f'npx cdk bootstrap --app "substrate {self.tool.name} -c {self.path} synth"',  # noqa: E501
			check=True,
			shell=True
		)

		subprocess.run(
			f'npx cdk deploy --require-approval never --app "substrate {self.tool.name} -c {self.path} synth"',  # noqa: E501
			check=True,
			shell=True
		)

		location = subprocess.check_output(
			'aws ec2 describe-instances --filters Name=instance-state-name,Values=running Name=tag:Name,Values=substrate-stack/substrate-leader --query Reservations[*].Instances[*].[PublicIpAddress] --output text',  # noqa: E501
			shell=True
		).strip().decode('utf-8')

		print('The CloudFormation stack has successfully deployed.')  # noqa: E501
		print('\033[91mIt may take several minutes before the instance is ready to use, please wait while the instance starts.\033[0m')  # noqa: E501
		while True:
			print('Checking if AWS instance is ready…', end='')
			try:
				response = requests.get(f'http://{location}')
				if response.status_code == 200:
					break
			except requests.exceptions.ConnectionError:
				pass

			print("instance isn't ready yet. Trying again in 30 seconds.")
			sleep(30)
		print('✓')

		return location

	def stop(self):
		subprocess.run(
			f'npx cdk destroy --force --app "substrate {self.tool.name} -c {self.path} synth"',  # noqa: E501
			check=True,
			shell=True
		)
		subprocess.run(
			f'aws s3 rm s3://{self.config["aws"]["bucket"]} --recursive',
			check=True,
			shell=True
		)


class _AWSStack(Stack):  # pylint: disable=too-many-instance-attributes
	def __init__(self, scope, _id, tool, config, data_urls, **kwargs):
		self.tool = tool
		self.config = config
		self.data_urls = data_urls
		self.leader_name = ''

		self.tool.upload_to_s3()

		super().__init__(scope, _id, **kwargs)

		self.vpc = ec2.Vpc(
			self,
			_id,
			max_azs=1,
			nat_gateways=0,
			subnet_configuration=[
				ec2.SubnetConfiguration(name='public', subnet_type=ec2.SubnetType.PUBLIC)
			]
		)

		ami_string = self.config['aws'].get('ami', None)
		if ami_string:
			self.ami = ec2.MachineImage.generic_linux({
				self.config['aws'].get('region', 'us-east-1'): 'ami-048ff3da02834afdc'
			})
		else:
			self.ami = ec2.MachineImage.latest_amazon_linux(
				generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
			)

		role_arn = self.config['aws'].get('role_arn', None)
		if role_arn:
			self.role = iam.Role.from_role_arn(self, 'john', role_arn, mutable=False)
		else:
			self.role = None

		self.file_system = self.provision_fs()
		self.provision_ec2()

	def add_leader_commands(self, udata, *args):
		for command in args:
			udata.add_commands(command)

			if self.config['aws'].get('save_logs', True):
				udata.add_commands(f'aws s3 sync /var/log s3://{self.config["aws"]["bucket"]}/logs')  # noqa: E501

	def get_udata(self, _type):
		udata = ec2.UserData.for_linux()
		self.add_leader_commands(
			udata,
			f'export AWS_DEFAULT_REGION={self.config["aws"].get("region", "us-east-1")}',  # noqa: E501
			f'export AWS_ACCESS_KEY_ID={os.environ.get("AWS_ACCESS_KEY_ID")}',
			f'export AWS_SECRET_ACCESS_KEY={os.environ.get("AWS_SECRET_ACCESS_KEY")}',
			f'export AWS_SESSION_TOKEN={os.environ.get("AWS_SESSION_TOKEN", "")}',
			'sudo yum check-update -y',
			'sudo yum upgrade -y',
			'sudo amazon-linux-extras install docker',
			'sudo service docker start',
			'sudo usermod -a -G docker ec2-user',
			'sudo yum install -y amazon-efs-utils',
			'sudo yum install -y nfs-utils',
			'sudo yum install -y python3',
			'sudo mkdir -p "/mnt/efs"',
			f'test -f "/sbin/mount.efs" && echo "{self.file_system.file_system_id}:/ /mnt/efs efs defaults,_netdev" >> /etc/fstab || echo "{self.file_system.file_system_id}.efs.{self.config["aws"].get("region", "us-east-1")}.amazonaws.com:/ /mnt/efs nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport,_netdev 0 0" >> /etc/fstab',  # noqa: E501
			'mount -a -t efs,nfs4 defaults',
			'until mountpoint -d /mnt/efs; do mount -a -t efs,nfs4 defaults; done'
		)

		if _type == 'leader':
			self.add_leader_commands(
				udata,
				'sudo mkdir -p /etc/pki/tls/private',
				'cd /etc/pki/tls/private',
				'sudo openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/C=US/ST=Tennessee/L=Knoxville/O=University of Tennessee/OU=Seelab/CN=github.com\/seelabutk"'  # pylint: disable=anomalous-backslash-in-string # noqa: E501,W605
			)

			self.add_leader_commands(
				udata,
				f'aws s3 sync s3://{self.config["aws"]["bucket"]} /mnt/efs',
				'cd /mnt/efs/data',
				*[f'curl -O {data_url}' for data_url in self.data_urls],
				'cd -'
			)

			self.add_leader_commands(
				udata,
				'mkdir /mnt/efs/swarm',
				'docker swarm init',
				'docker swarm join-token worker | grep "docker" > /mnt/efs/swarm/worker',
				'docker swarm join-token manager | grep "docker" > /mnt/efs/swarm/manager',
				self.tool.service_command
			)
		elif _type == 'manager':
			udata.add_commands('until [ -f /mnt/efs/swarm/manager ]; do sleep 1; done')
			udata.add_commands('$(cat /mnt/efs/swarm/manager)')
		elif _type == 'worker':
			udata.add_commands('until [ -f /mnt/efs/swarm/worker ]; do sleep 1; done')
			udata.add_commands('$(cat /mnt/efs/swarm/worker)')

		return udata

	def provision_ec2(self):
		managers = self.config['aws'].get('managers', {})
		workers = self.config['aws'].get('workers', {})

		nodes = []
		for index, _type in enumerate(managers):
			count = managers.get(_type, 1)
			for index2 in range(count):
				if index == 0 and index2 == 0:
					instance_name = 'substrate-leader'
					udata = self.get_udata('leader')
				else:
					instance_name = f'substrate-manager-{_type}-{index}'
					udata = self.get_udata('manager')

				nodes.append(ec2.Instance(
					self,
					instance_name,
					instance_type=ec2.InstanceType(instance_type_identifier=_type),
					machine_image=self.ami,
					role=self.role,
					user_data=udata,
					vpc=self.vpc,
					vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
				))

		for _type in workers:
			udata = self.get_udata('worker')

			count = workers.get(_type, 1)
			for index in range(count):
				nodes.append(ec2.Instance(
					self,
					f'substrate-worker-{_type}-{index}',
					instance_type=ec2.InstanceType(instance_type_identifier=_type),
					machine_image=self.ami,
					role=self.role,
					user_data=udata,
					vpc=self.vpc,
					vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
				))

		for node in nodes:
			node.node.add_dependency(self.file_system.mount_targets_available)

			if self.role:
				node.instance.iam_instance_profile = None
				node.node.try_remove_child('InstanceProfile')

			# TODO: fix
			node.connections.allow_from_any_ipv4(
				ec2.Port.all_traffic(),
				'General Purpose'
			)

	def provision_fs(self):
		efs_sg = ec2.SecurityGroup(self, 'substrate-efs-sg', vpc=self.vpc)
		efs_sg.add_ingress_rule(
			peer=ec2.Peer.any_ipv4(),  # TODO: fix
			connection=ec2.Port.tcp(2049)
		)

		return efs.FileSystem(
			self,
			'substrate-efs',
			removal_policy=RemovalPolicy.DESTROY,
			security_group=efs_sg,
			vpc=self.vpc
		)
