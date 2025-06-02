# Docker Image Build & Push Workflow for Automa Backend


## Pre-requisites (One-Time Setup)

### Login to Google Cloud

`gcloud auth login`
`gcloud config set project automa-development`

### Enable Artifact Registry API

`gcloud services enable artifactregistry.googleapis.com` 

### Configure Docker authentication

`gcloud auth configure-docker asia-south1-docker.pkg.dev`

### Build Docker Image

From the project root (where Dockerfile exists):

`docker build -t asia-south1-docker.pkg.dev/automa-development/automa-repo/automa-backend:v1.0.4 .`


(Optional) Tag the Image

If not tagged during build:

`docker tag <local-image-id-or-name> asia-south1-docker.pkg.dev/automa-development/automa-repo/automa-backend:v1.0.4`


Check image IDs:

`docker images`


### Push Image to Artifact Registry

`docker push asia-south1-docker.pkg.dev/automa-development/automa-repo/automa-backend:v1.0.4`


### Verify Uploaded Image (Optional)

`gcloud artifacts docker images list asia-south1-docker.pkg.dev/automa-development/automa-repo`
