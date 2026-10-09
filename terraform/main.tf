terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_dynamodb_table" "poses" {
  name         = "flowforge-poses"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pose_id"

  attribute {
    name = "pose_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "flows" {
  name         = "flowforge-flows"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "flow_id"

  attribute {
    name = "flow_id"
    type = "S"
  }
}
