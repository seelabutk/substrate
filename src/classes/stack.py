from aws_cdk import Stack, aws_ec2 as ec2


class SubstrateStack(Stack):
	def __init__(self, scope, _id, **kwargs):
		config = kwargs.pop('config').get('aws')

		super().__init__(scope, _id, **kwargs)

		vpc = ec2.Vpc(
			self,
			_id,
			nat_gateways=0,
			subnet_configuration=[
				ec2.SubnetConfiguration(name='public', subnet_type=ec2.SubnetType.PUBLIC),
				ec2.SubnetConfiguration(
					name='isolated',
					subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
				)
			]
		)

		ami = ec2.MachineImage.latest_amazon_linux(
			generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
			edition=ec2.AmazonLinuxEdition.STANDARD,
			virtualization=ec2.AmazonLinuxVirt.HVM,
			storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
		)

		managers = config.get('managers', {})
		workers = config.get('workers', {})

		nodes = []
		for _type in managers:
			count = managers.get(_type, 0)
			for index in range(count):
				nodes.append(ec2.Instance(
					self,
					f'substrate-manager-{_type}-{index}',
					instance_type=ec2.InstanceType(instance_type_identifier=_type),
					machine_image=ami,
					vpc=vpc,
					vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
				))

		for _type in workers:
			count = workers.get(_type, 0)
			for index in range(count):
				nodes.append(ec2.Instance(
					self,
					f'substrate-worker-{_type}-{index}',
					instance_type=ec2.InstanceType(instance_type_identifier=_type),
					machine_image=ami,
					vpc=vpc,
					vpc_subnets=ec2.SubnetSelection(
						subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
					)
				))

		for node in nodes:
			node.connections.allow_from_any_ipv4(
				ec2.Port.all_traffic(),
				'General Purpose'
			)
