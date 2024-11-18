resource "google_artifact_registry_repository" "docker_repo" {
  repository_id   = var.project    # Unique name for your repository
  location        = var.region        # Region for your repository
  format          = "DOCKER"         # Specify that this repository will store Docker images
  description     = "Docker repository for storing images"
  labels = {
    environment = "production"
  }
}