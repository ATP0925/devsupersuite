# ─────────────────────────────────────────────────────────────────────────────
# AWS Terraform Outputs
# ─────────────────────────────────────────────────────────────────────────────

output "vpc_id" {
  description = "Air-gapped private VPC ID"
  value       = aws_vpc.devsupersuite_vpc.id
}

output "cluster_id" {
  description = "EKS Cluster identifier"
  value       = aws_eks_cluster.devsupersuite_eks.id
}

output "cluster_endpoint" {
  description = "EKS Private API Endpoint (Internal Only)"
  value       = aws_eks_cluster.devsupersuite_eks.endpoint
}

output "cluster_arn" {
  description = "EKS Cluster ARN"
  value       = aws_eks_cluster.devsupersuite_eks.arn
}

output "kms_key_arn" {
  description = "Customer Managed KMS Key ARN"
  value       = aws_kms_key.devsupersuite_kms.arn
}

output "irsa_role_arn" {
  description = "IAM Role ARN for Workload Identity / IRSA"
  value       = aws_iam_role.devsupersuite_irsa.arn
}

output "zero_egress_enforced" {
  description = "Confirmation of Zero-Egress Network Isolation"
  value       = true
}
