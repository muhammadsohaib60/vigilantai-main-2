variable "region" {
  description = "The region where resources will be deployed"
  type        = string
  default     = "us-east1"
}

variable "project" {
  description = "The GCP project ID"
  type        = string
  default     = "dark-garden-416321"
}

variable "sa" {
  description = "The name of the service account"
  type        = string
  default     = "vigilantai"
}

variable "vectorcollection" {
  description = "The name of the Firestore collection to store vector data"
  type        = string
  default     = "secondaryemail"
}