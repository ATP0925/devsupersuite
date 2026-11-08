# ─────────────────────────────────────────────────────────────────────────────
# Azure NSG - Zero-Egress Air-Gap Invariant Configuration
# Reference: DSS-IAC-AZURE-SEC-2026-V1
# ─────────────────────────────────────────────────────────────────────────────

resource "azurerm_network_security_group" "aks_nsg" {
  name                = "${var.cluster_name}-nsg"
  location            = azurerm_resource_group.devsupersuite_rg.location
  resource_group_name = azurerm_resource_group.devsupersuite_rg.name

  # Inbound Rules
  security_rule {
    name                       = "Allow-Internal-VNet-Inbound"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges     = ["443", "8443", "8080"]
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }

  # Outbound Rule: Allow internal VNet routing
  security_rule {
    name                       = "Allow-Internal-VNet-Outbound"
    priority                   = 100
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }

  # Zero-Egress Invariant: Deny All Outbound to Public Internet
  security_rule {
    name                       = "Deny-All-Internet-Outbound"
    priority                   = 4096
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
  }

  tags = {
    Name   = "${var.cluster_name}-nsg"
    AirGap = "true"
  }
}

resource "azurerm_subnet_network_security_group_association" "aks_nsg_assoc" {
  subnet_id                 = azurerm_subnet.aks_subnet.id
  network_security_group_id = azurerm_network_security_group.aks_nsg.id
}
