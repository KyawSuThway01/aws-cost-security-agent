terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-southeast-2"
}

# Only asks "who am I". It creates nothing.
data "aws_caller_identity" "current" {}

output "caller_arn" {
  value = data.aws_caller_identity.current.arn
}

# Where the weekly report will be sent. Name starts with "aws-agent-" because
# the deploy role is only allowed to manage topics with that prefix.
resource "aws_sns_topic" "reports" {
  name = "aws-agent-reports"
}

output "topic_arn" {
  value = aws_sns_topic.reports.arn
}