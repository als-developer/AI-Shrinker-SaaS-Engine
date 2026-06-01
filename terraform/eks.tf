# EKS Cluster Configuration for Sovereign Grid
# Version: 31.0

module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.28"

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    main = {
      name = "sovereign-grid-nodes"

      instance_types = var.node_instance_types

      min_size     = var.min_capacity
      max_size     = var.max_capacity
      desired_size = var.desired_capacity

      vpc_security_group_ids = [aws_security_group.eks_nodes.id]

      tags = {
        "k8s.io/cluster-autoscaler/enabled" = "true"
        "k8s.io/cluster-autoscaler/${var.cluster_name}" = "owned"
      }
    }
  }

  tags = var.tags
}

# Cluster Autoscaler IAM Policy
resource "aws_iam_policy" "cluster_autoscaler" {
  name        = "${var.project_name}-cluster-autoscaler"
  description = "Policy for cluster autoscaler"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeTags",
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup",
          "ec2:DescribeLaunchTemplateVersions"
        ]
        Resource = ["*"]
      }
    ]
  })
}

# Attach policy to node group role
resource "aws_iam_role_policy_attachment" "cluster_autoscaler" {
  policy_arn = aws_iam_policy.cluster_autoscaler.arn
  role       = module.eks.eks_managed_node_groups["main"].iam_role_name
}
