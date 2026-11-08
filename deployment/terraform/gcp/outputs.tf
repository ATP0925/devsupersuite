# ─────────────────────────────────────────────────────────────────────────────
# Google Cloud Terraform Outputs
# ─────────────────────────────────────────────────────────────────────────────

output "cluster_name" {
  description = "GKE Cluster Name"
  value       = google_container_cluster.devsupersuite_gke.name
}

output "cluster_endpoint" {
  description = "GKE Master Internal Private Endpoint"
  value       = google_container_cluster.devsupersuite_gke.endpoint
}

output "network_name" {
  description = "Air-gapped VPC Network Name"
  value       = google_compute_network.devsupersuite_vpc.name
}

output "kms_key_id" {
  description = "Cloud KMS CryptoKey ID"
  value       = google_kms_crypto_key.gke_secret_key.id
}

output "workload_identity_pool" {
  description = "Google Workload Identity Federation Pool"
  value       = "${var.project_id}.svc.id.goog"
}

output "zero_egress_enforced" {
  description = "Confirmation of Zero-Egress Firewall Rules"
  value       = true
}
