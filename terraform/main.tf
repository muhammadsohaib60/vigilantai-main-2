terraform {
  backend "gcs" {
    bucket  = "vigilantai-terraform"
    prefix  = "vigilantai/state"
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

resource "google_service_account" "vigilantai" {
  account_id   = var.sa
  display_name = "vigilantai Service Account"
}

# Bind required roles to the service account
resource "google_project_iam_member" "vertex_ai_permission" {
  project = var.project
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vigilantai.email}"
}

resource "google_project_iam_member" "firebase_permission" {
  project = var.project
  role    = "roles/firebase.admin"
  member  = "serviceAccount:${google_service_account.vigilantai.email}"
}

resource "google_project_iam_member" "firestore_permission" {
  project = var.project
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${google_service_account.vigilantai.email}"
}

resource "google_project_iam_member" "gcs_permission" {
  project = var.project
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.vigilantai.email}"
}

resource "google_project_iam_member" "cloud_run_permission" {
  project = var.project
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.vigilantai.email}"
}

resource "google_project_iam_member" "cloud_run_service_account_user" {
  project = var.project
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.vigilantai.email}"
}

resource "google_project_iam_member" "artifact_registry_writer" {
  project = var.project
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.vigilantai.email}"
}

# Generate a key for the service account
resource "google_service_account_key" "service_account_key" {
  service_account_id = google_service_account.vigilantai.name
  public_key_type    = "TYPE_X509_PEM_FILE"
  
  # Optionally specify where to store the key file
  private_key_type   = "TYPE_GOOGLE_CREDENTIALS_FILE"
}

# Output the key content to a file on the local system
resource "local_file" "service_account_key_file" {
  content  = google_service_account_key.service_account_key.private_key
  filename = "${path.module}/VIGILANTAI_SERVICE_ACCOUNT_KEY.json"  # Save it in the current module directory
}


output "service_account_email" {
  value = google_service_account.vigilantai.email
}
