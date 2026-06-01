# Terraform Variables for Sovereign Grid Infrastructure
# Version: 31.0

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for primary deployment"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "sovereign-grid"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Number of availability zones to use"
  type        = number
  default     = 3
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "sovereign-grid-eks"
}

variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "sovereigngrid.com"
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS nodes"
  type        = list(string)
  default     = ["t3.medium", "t3.large"]
}

variable "desired_capacity" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "max_capacity" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 20
}

variable "min_capacity" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 3
}

# Database configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.large"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "sovereign_grid"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

# Redis configuration
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 1
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Environment = "production"
    Project     = "SovereignGrid"
    ManagedBy   = "Terraform"
  }
}
