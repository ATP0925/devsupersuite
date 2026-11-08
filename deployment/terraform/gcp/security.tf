# ─────────────────────────────────────────────────────────────────────────────
# Google Cloud VPC Firewall - Zero-Egress Air-Gap Security Invariants
# Reference: DSS-IAC-GCP-SEC-2026-V1
# ─────────────────────────────────────────────────────────────────────────────

# 1. Deny All Outbound Egress to Public Internet (Zero-Egress Invariant)
resource "google_compute_firewall" "deny_all_external_egress" {
  name      = "${var.cluster_name}-deny-all-egress"
  network   = google_compute_network.devsupersuite_vpc.name
  project   = var.project_id
  direction = "EGRESS"
  priority  = 65534

  # Target all external IPv4 space
  destination_ranges = ["0.0.0.0/0"]

  deny {
    protocol = "all"
  }
}

# 2. Allow Internal Intra-VPC and GKE Pod Egress Only
resource "google_compute_firewall" "allow_internal_egress" {
  name      = "${var.cluster_name}-allow-internal-egress"
  network   = google_compute_network.devsupersuite_vpc.name
  project   = var.project_id
  direction = "EGRESS"
  priority  = 1000

  destination_ranges = [
    var.vpc_cidr,
    var.pod_cidr,
    var.service_cidr,
    var.master_cidr
  ]

  allow {
    protocol = "all"
  }
}

# 3. Restrict Ingress strictly to Internal Corporate Subnet
resource "google_compute_firewall" "allow_internal_ingress" {
  name      = "${var.cluster_name}-allow-internal-ingress"
  network   = google_compute_network.devsupersuite_vpc.name
  project   = var.project_id
  direction = "INGRESS"
  priority  = 1000

  source_ranges = [
    var.vpc_cidr,
    var.pod_cidr,
    var.master_cidr
  ]

  allow {
    protocol = "tcp"
    ports    = ["443", "8443", "8080", "10250"]
  }

  allow {
    protocol = "icmp"
  }
}
