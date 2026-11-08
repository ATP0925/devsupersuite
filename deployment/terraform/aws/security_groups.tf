# ─────────────────────────────────────────────────────────────────────────────
# AWS Security Groups - Zero-Egress Air-Gap Invariant Configuration
# Reference: DSS-IAC-AWS-SEC-2026-V1
# ─────────────────────────────────────────────────────────────────────────────

# 1. EKS Control Plane Security Group
resource "aws_security_group" "eks_cluster_sg" {
  name        = "${var.cluster_name}-control-plane-sg"
  description = "EKS Cluster Control Plane Security Group (Air-Gapped)"
  vpc_id      = aws_vpc.devsupersuite_vpc.id

  # Ingress strictly from internal VPC CIDR
  ingress {
    description = "Allow HTTPS API access from private corporate VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Egress strictly internal to VPC CIDR (NO 0.0.0.0/0 RULE)
  egress {
    description = "Strict intra-VPC control plane egress"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name   = "${var.cluster_name}-control-plane-sg"
    AirGap = "true"
  }
}

# 2. Worker Node Security Group
resource "aws_security_group" "eks_node_sg" {
  name        = "${var.cluster_name}-node-sg"
  description = "EKS Worker Node Security Group (Zero-Egress)"
  vpc_id      = aws_vpc.devsupersuite_vpc.id

  ingress {
    description = "Allow intra-cluster node communication"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  ingress {
    description = "Allow control plane to node kubelet"
    from_port   = 10250
    to_port     = 10250
    protocol    = "tcp"
    security_groups = [aws_security_group.eks_cluster_sg.id]
  }

  # Egress strictly restricted to VPC CIDR (NO 0.0.0.0/0)
  egress {
    description = "Strict intra-VPC node egress only"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name   = "${var.cluster_name}-node-sg"
    AirGap = "true"
  }
}

# 3. VPC Endpoints Security Group
resource "aws_security_group" "vpc_endpoints_sg" {
  name        = "${var.cluster_name}-endpoints-sg"
  description = "Private VPC Interface Endpoints Security Group"
  vpc_id      = aws_vpc.devsupersuite_vpc.id

  ingress {
    description = "Allow HTTPS from private VPC nodes"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Endpoint internal response routing"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name   = "${var.cluster_name}-endpoints-sg"
    AirGap = "true"
  }
}
