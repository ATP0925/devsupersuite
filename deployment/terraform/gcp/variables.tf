# ─────────────────────────────────────────────────────────────────────────────
# Google Cloud GKE - Terraform Variables
# ─────────────────────────────────────────────────────────────────────────────

variable "project_id" {
  type        = string
  description = "Google Cloud Project ID"
  default     = "devsupersuite-enterprise-sovereign"
}

variable "region" {
  type        = string
  description = "Target GCP Region"
  default     = "us-central1"
}

variable "cluster_name" {
  type        = string
  description = "Identifier for GKE cluster and network"
  default     = "devsupersuite-sovereign-gke"
}

variable "environment" {
  type        = string
  description = "Deployment Environment"
  default     = "enterprise-airgap"
}

variable "vpc_cidr" {
  type        = string
  description = "Primary subnet CIDR block"
  default     = "10.200.0.0/20"
}

variable "pod_cidr" {
  type        = string
  description = "Secondary CIDR block for Kubernetes Pods"
  default     = "10.201.0.0/16"
}

variable "service_cidr" {
  type        = string
  description = "Secondary CIDR block for Kubernetes Services"
  default     = "10.202.0.0/20"
}

variable "master_cidr" {
  type        = string
  description = "Master control plane CIDR (/28)"
  default     = "172.16.0.0/28"
}

variable "machine_type" {
  type        = string
  description = "Compute Engine instance type for worker nodes"
  default     = "e2-standard-8"
}

variable "node_count" {
  type        = number
  description = "Number of worker nodes per zone"
  default     = 3
}
