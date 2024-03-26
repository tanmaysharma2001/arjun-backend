terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }
}


variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

provider "aws" {
  region = var.aws_region
}

# Create a security group that allows SSH and HTTP traffic
resource "aws_security_group" "allow_ssh_http" {
  name        = "allow_ssh_http"
  description = "Allow SSH and HTTP inbound traffic"

  ingress {
    description = "SSH from ALL"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    description = "HTTP from ALL"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}

resource "aws_instance" "server_python" {
  ami           = "ami-0faab6bdbac9486fb"
  instance_type = "c5.2xlarge"
  key_name = aws_key_pair.deployer.key_name
  security_groups = [aws_security_group.allow_ssh_http.name]
  user_data = <<-EOF
              #!/bin/bash
              sudo apt update -y
              sudo apt install -y python3-pip make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev openssl
              curl https://pyenv.run | bash
              echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
              echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
              echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n eval "$(pyenv init -)"\nfi' >> ~/.bashrc
              EOF

  tags = {
    Name = "server-python"
  }
}

resource "aws_key_pair" "deployer" {
  key_name   = "deployer"
  public_key = file("~/.ssh/id_rsa.pub")
}

output "aws-1-public-ip" {
    value = aws_instance.server_python.public_ip
}
