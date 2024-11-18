# Define Firestore Database
resource "google_firestore_database" "firestore_db" {
  project  = var.project
  name     = "(default)"  # Firestore default database
  location_id = var.region
  type     = "FIRESTORE_NATIVE"

  delete_protection_state = "DELETE_PROTECTION_DISABLED"
  deletion_policy         = "DELETE"
}

# Firestore Index with vector embeddings
resource "google_firestore_index" "vector-index" {
  project     = var.project
  database   = google_firestore_database.firestore_db.name
  collection = var.vectorcollection
  depends_on = [ google_firestore_database.firestore_db ]

  fields {
    field_path = "__name__"
    order      = "ASCENDING"
  }

  fields {
    field_path = "embedding"
    vector_config {
      dimension = 768
      flat {}
    }
  }
}

output "firestore_vector_index_id" {
  value = google_firestore_index.vector-index.id
}
