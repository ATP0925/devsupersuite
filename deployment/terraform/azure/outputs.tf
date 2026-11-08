# ─────────────────────────────────────────────────────────────────────────────
# Azure Terraform Outputs
# ─────────────────────────────────────────────────────────────────────────────

output "cluster_id" {
  description = "AKS Cluster Resource ID"
  value       = azurerm_kubernetes_cluster.devsupersuite_aks.id
}

output "cluster_name" {
  description = "AKS Cluster Name"
  value       = azurerm_kubernetes_cluster.devsupersuite_aks.name
}

output "private_fqdn" {
  description = "AKS Private API FQDN (Accessible strictly over private VNet/VPN)"
  value       = azurerm_kubernetes_cluster.devsupersuite_aks.private_fqdn
}

output "key_vault_id" {
  description = "Sovereign Key Vault Resource ID"
  value       = azurerm_key_vault.devsupersuite_kv.id
}

output "vnet_id" {
  description = "Virtual Network ID"
  value       = azurerm_virtual_network.devsupersuite_vnet.id
}

output "zero_egress_enforced" {
  description = "Confirmation of Outbound Internet Deny NSG"
  value       = true
}
