# ─────────────────────────────────────────────────────────────────────────────
# DevSuperSuite Sovereign Enterprise Infrastructure as Code (AWS GovCloud / EKS)
# Architecture: Air-Gapped Private VPC with Zero Public Internet Access
# Reference: DSS-IAC-AWS-2026-V1
# Contact: DevSuperSuite Cloud Architecture (cloud@devsupersuite.com)
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
  }
}

# 1. Sovereign KMS Customer-Managed Key (CMK)
resource "aws_kms_key" "devsupersuite_kms" {
  description             = "DevSuperSuite Sovereign CMK for EKS Secrets and Storage Encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Environment = var.environment
    Compliance  = "NIST-800-171-Rev2"
    ManagedBy   = "DevSuperSuite-Terraform"
  }
}

resource "aws_kms_alias" "devsupersuite_kms_alias" {
  name          = "alias/${var.cluster_name}-key"
  target_key_id = aws_kms_key.devsupersuite_kms.key_id
}

# 2. Air-Gapped Private VPC (Zero Internet Gateway Attached)
resource "aws_vpc" "devsupersuite_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.cluster_name}-vpc"
    Environment = var.environment
    AirGap      = "true"
  }
}

# Isolated Private Subnets across 3 Availability Zones
resource "aws_subnet" "private_subnets" {
  count             = 3
  vpc_id            = aws_vpc.devsupersuite_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = element(var.availability_zones, count.index)

  tags = {
    Name                              = "${var.cluster_name}-private-${count.index + 1}"
    "kubernetes.io/role/internal-elb" = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "owned"
  }
}

resource "aws_route_table" "isolated_rt" {
  vpc_id = aws_vpc.devsupersuite_vpc.id

  tags = {
    Name   = "${var.cluster_name}-isolated-rt"
    AirGap = "true"
  }
}

resource "aws_route_table_association" "isolated_assoc" {
  count          = 3
  subnet_id      = aws_subnet.private_subnets[count.index].id
  route_table_id = aws_route_table.isolated_rt.id
}

# 3. VPC Interface Endpoints (Sovereign In-VPC AWS Services, Zero Public Routing)
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.devsupersuite_vpc.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private_subnets[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.devsupersuite_vpc.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private_subnets[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "kms" {
  vpc_id              = aws_vpc.devsupersuite_vpc.id
  service_name        = "com.amazonaws.${var.aws_region}.kms"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private_subnets[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true
}

# 4. IAM Role for EKS Cluster Control Plane
resource "aws_iam_role" "eks_cluster_role" {
  name = "${var.cluster_name}-control-plane-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws-us-gov:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

# 5. Air-Gapped Private EKS Cluster
resource "aws_eks_cluster" "devsupersuite_eks" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = aws_subnet.private_subnets[*].id
    endpoint_private_access = true
    endpoint_public_access  = false # ZERO PUBLIC INTERNET EXPOSURE
    security_group_ids      = [aws_security_group.eks_cluster_sg.id]
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.devsupersuite_kms.arn
    }
    resources = ["secrets"]
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]

  tags = {
    Environment = var.environment
    AirGap      = "true"
  }
}

# 6. IAM Roles for Service Accounts (IRSA)
resource "aws_iam_role" "devsupersuite_irsa" {
  name = "${var.cluster_name}-irsa-workload"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws-us-gov:iam::${var.aws_account_id}:oidc-provider/${replace(aws_eks_cluster.devsupersuite_eks.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.devsupersuite_eks.identity[0].oidc[0].issuer, "https://", "")}:sub" : "system:serviceaccount:devsupersuite-sovereign:devsupersuite-core"
          }
        }
      }
    ]
  })
}

# 7. Private EKS Managed Node Group
resource "aws_iam_role" "eks_node_role" {
  name = "${var.cluster_name}-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_eks_node_group" "devsupersuite_nodes" {
  cluster_name    = aws_eks_cluster.devsupersuite_eks.name
  node_group_name = "${var.cluster_name}-worker-pool"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = aws_subnet.private_subnets[*].id
  instance_types  = var.node_instance_types

  scaling_config {
    desired_size = var.desired_nodes
    max_size     = var.max_nodes
    min_size     = var.min_nodes
  }

  tags = {
    Environment = var.environment
    AirGap      = "true"
  }
}
