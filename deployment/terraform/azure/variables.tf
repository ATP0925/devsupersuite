# ─────────────────────────────────────────────────────────────────────────────
# Azure AKS - Terraform Variables
# ─────────────────────────────────────────────────────────────────────────────

variable "resource_group_name" {
  type        = string
  description = "Target Azure Resource Group Name"
  default     = "rg-devsupersuite-sovereign-usgov"
}

variable "location" {
  type        = string
  description = "Azure Region (e.g. usgovvirginia, eastus2)"
  default     = "usgovvirginia"
}

variable "cluster_name" {
  type        = string
  description = "Identifier for AKS Cluster and Associated Resources"
  default     = "dss-sovereign-aks"
}

variable "environment" {
  type        = string
  description = "Deployment Tier"
  default     = "enterprise-airgap"
}

variable "kubernetes_version" {
  type        = string
  description = "Target AKS Kubernetes version"
  default     = "1.30"
}

variable "vnet_cidr" {
  type        = string
  description = "Virtual Network CIDR block"
  default     = "10.150.0.0/16"
}

variable "subnet_cidr" {
  type        = string
  description = "AKS Node Subnet CIDR block"
  default     = "10.150.1.0/24"
}

variable "vm_size" {
  type        = string
  description = "Virtual Machine Size for AKS Nodes"
  default     = "Standard_D8s_v5"
}

variable "node_count" {
  type        = number
  description = "Initial Node Count"
  default     = 3
}
