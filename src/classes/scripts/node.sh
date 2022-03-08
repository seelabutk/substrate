sudo yum update -y
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user

sudo yum install -y amazon-efs-utils
sudo yum install -y python3

EFS_ID=$(aws efs describe-file-systems | python3 -c "import json, sys; efs = json.load(sys.stdin)['FileSystems']; print(next((fs for fs in efs if fs['Name'] == 'substrate-stack/substrate-efs'), None)['FileSystemId']);")
EFS_IP=$(aws efs describe-mount-targets --file-system-id $EFS_ID | python3 -c "import json, sys; print(json.load(sys.stdin)['MountTargets'][0]['IpAddress'])")

sudo mkdir /mnt/efs
sudo mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $EFS_IP:/ /mnt/efs
