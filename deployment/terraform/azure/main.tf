# ─────────────────────────────────────────────────────────────────────────────
# DevSuperSuite Sovereign Enterprise Infrastructure as Code (Azure AKS)
# Architecture: Air-Gapped Private AKS with Azure Key Vault & Calico Policies
# Reference: DSS-IAC-AZURE-2026-V1
# Contact: DevSuperSuite Cloud Architecture (cloud@devsupersuite.com)
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }
  }
}

# 1. Resource Group
resource "azurerm_resource_group" "devsupersuite_rg" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = var.environment
    Compliance  = "NIST-800-171-Rev2"
    AirGap      = "true"
  }
}

# 2. Virtual Network & Isolated Subnet
resource "azurerm_virtual_network" "devsupersuite_vnet" {
  name                = "${var.cluster_name}-vnet"
  location            = azurerm_resource_group.devsupersuite_rg.location
  resource_group_name = azurerm_resource_group.devsupersuite_rg.name
  address_space       = [var.vnet_cidr]

  tags = {
    Environment = var.environment
    AirGap      = "true"
  }
}

resource "azurerm_subnet" "aks_subnet" {
  name                 = "${var.cluster_name}-aks-subnet"
  resource_group_name  = azurerm_resource_group.devsupersuite_rg.name
  virtual_network_name = azurerm_virtual_network.devsupersuite_vnet.name
  address_prefixes     = [var.subnet_cidr]

  private_endpoint_network_policies_enabled = true
}

# 3. Azure Key Vault (HSM Sovereign Encryption)
data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "devsupersuite_kv" {
  name                        = "${substr(replace(var.cluster_name, "-", ""), 0, 20)}kv"
  location                    = azurerm_resource_group.devsupersuite_rg.location
  resource_group_name         = azurerm_resource_group.devsupersuite_rg.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "premium"
  soft_delete_retention_days  = 90
  purge_protection_enabled    = true

  network_acls {
    bypass         = "AzureServices"
    default_action = "Deny"
    virtual_network_subnet_ids = [azurerm_subnet.aks_subnet.id]
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_key_vault_key" "aks_etcd_key" {
  name         = "${var.cluster_name}-etcd-key"
  key_vault_id = azurerm_key_vault.devsupersuite_kv.id
  key_type     = "RSA-HSM"
  key_size     = 3072

  key_opts = [
    "decrypt",
    "encrypt",
    "sign",
    "unwrapKey",
    "verify",
    "wrapKey"
  ]
}

# 4. Managed Identity for Workload Federation
resource "azurerm_user_assigned_identity" "aks_identity" {
  name                = "${var.cluster_name}-control-identity"
  location            = azurerm_resource_group.devsupersuite_rg.location
  resource_group_name = azurerm_resource_group.devsupersuite_rg.name
}

# 5. Private Air-Gapped AKS Cluster
resource "azurerm_kubernetes_cluster" "devsupersuite_aks" {
  name                    = var.cluster_name
  location                = azurerm_resource_group.devsupersuite_rg.location
  resource_group_name     = azurerm_resource_group.devsupersuite_rg.name
  dns_prefix_private_cluster = "${var.cluster_name}-priv"
  private_cluster_enabled = true # ZERO PUBLIC FQDN
  private_dns_zone_id     = "System"
  kubernetes_version      = var.kubernetes_version

  default_node_pool {
    name           = "workloadpool"
    node_count     = var.node_count
    vm_size        = var.vm_size
    vnet_subnet_id = azurerm_subnet.aks_subnet.id
    os_disk_type   = "Managed"
    os_disk_size_gb = 128

    node_labels = {
      "environment" = var.environment
      "airgap"      = "true"
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks_identity.id]
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "calico"
    outbound_type  = "userDefinedRouting" # NO PUBLIC LOAD BALANCER EGRESS
  }

  key_vault_secrets_provider {
    secret_rotation_enabled  = true
    secret_rotation_interval = "2m"
  }

  tags = {
    Environment = var.environment
    AirGap      = "true"
  }
}
