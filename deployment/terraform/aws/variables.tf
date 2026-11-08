# ─────────────────────────────────────────────────────────────────────────────
# AWS GovCloud / Commercial EKS - Terraform Variables
# ─────────────────────────────────────────────────────────────────────────────

variable "aws_region" {
  type        = string
  description = "AWS Target Region (e.g. us-gov-west-1 or us-east-1)"
  default     = "us-gov-west-1"
}

variable "aws_account_id" {
  type        = string
  description = "Target AWS Account ID"
  default     = "123456789012"
}

variable "environment" {
  type        = string
  description = "Deployment tier"
  default     = "enterprise-airgap"
}

variable "cluster_name" {
  type        = string
  description = "Name identifier for EKS cluster and VPC resources"
  default     = "devsupersuite-sovereign-eks"
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes control plane version"
  default     = "1.30"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the air-gapped private VPC"
  default     = "10.100.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones for multi-AZ resiliency"
  default     = ["us-gov-west-1a", "us-gov-west-1b", "us-gov-west-1c"]
}

variable "node_instance_types" {
  type        = list(string)
  description = "EC2 instance types for EKS worker nodes"
  default     = ["m6i.2xlarge"]
}

variable "desired_nodes" {
  type        = number
  description = "Desired number of worker nodes"
  default     = 3
}

variable "min_nodes" {
  type        = number
  description = "Minimum number of worker nodes"
  default     = 2
}

variable "max_nodes" {
  type        = number
  description = "Maximum number of worker nodes"
  default     = 10
}
