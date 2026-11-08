# ─────────────────────────────────────────────────────────────────────────────
# DevSuperSuite Sovereign Enterprise Infrastructure as Code (Google Cloud GKE)
# Architecture: Air-Gapped Private GKE with Cloud KMS & Workload Identity
# Reference: DSS-IAC-GCP-2026-V1
# Contact: DevSuperSuite Cloud Architecture (cloud@devsupersuite.com)
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.15"
    }
  }
}

# 1. Cloud KMS KeyRing & Sovereign CryptoKey
resource "google_kms_key_ring" "devsupersuite_keyring" {
  name     = "${var.cluster_name}-keyring"
  location = var.region
  project  = var.project_id
}

resource "google_kms_crypto_key" "gke_secret_key" {
  name            = "${var.cluster_name}-crypto-key"
  key_ring        = google_kms_key_ring.devsupersuite_keyring.id
  rotation_period = "7776000s" # 90 days automatic rotation

  purpose = "ENCRYPT_DECRYPT"

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
}

# 2. Private VPC Network (No Auto-Subnets, Zero Internet Gateways)
resource "google_compute_network" "devsupersuite_vpc" {
  name                    = "${var.cluster_name}-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "devsupersuite_subnet" {
  name                     = "${var.cluster_name}-private-subnet"
  ip_cidr_range            = var.vpc_cidr
  region                   = var.region
  network                  = google_compute_network.devsupersuite_vpc.id
  private_ip_google_access = true
  project                  = var.project_id

  secondary_ip_range {
    range_name    = "gke-pods-range"
    ip_cidr_range = var.pod_cidr
  }

  secondary_ip_range {
    range_name    = "gke-services-range"
    ip_cidr_range = var.service_cidr
  }
}

# 3. Sovereign Private GKE Cluster
resource "google_container_cluster" "devsupersuite_gke" {
  name     = var.cluster_name
  location = var.region
  project  = var.project_id
  network  = google_compute_network.devsupersuite_vpc.name
  subnetwork = google_compute_subnetwork.devsupersuite_subnet.name

  remove_default_node_pool = true
  initial_node_count       = 1

  # Completely private nodes and control plane
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = true # ZERO PUBLIC ENDPOINT
    master_ipv4_cidr_block  = var.master_cidr
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = var.vpc_cidr
      display_name = "Corporate Private VPC"
    }
  }

  # Hardware Security Module / Cloud KMS Database Encryption
  database_encryption {
    state    = "ENCRYPTED"
    key_name = google_kms_crypto_key.gke_secret_key.id
  }

  # Google Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # In-cluster Calico / Datapath NetworkPolicy
  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  addons_config {
    network_policy_config {
      disabled = false
    }
    http_load_balancing {
      disabled = true # No external Google HTTP load balancer
    }
  }

  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"
}

# 4. Air-Gapped Dedicated Node Pool
resource "google_container_node_pool" "devsupersuite_nodes" {
  name       = "${var.cluster_name}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.devsupersuite_gke.name
  project    = var.project_id
  node_count = var.node_count

  node_config {
    machine_type = var.machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    # Conceal node metadata to enforce Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      environment = var.environment
      airgap      = "true"
    }
  }
}
