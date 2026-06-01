#!/bin/bash
# Production Deployment Script for Sovereign Grid
# Version: 31.0

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
REGION=${2:-eu-west-1}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOY_LOG="deploy_${TIMESTAMP}.log"

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOY_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOY_LOG"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$DEPLOY_LOG"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    command -v docker >/dev/null 2>&1 || error "Docker is required but not installed"
    command -v kubectl >/dev/null 2>&1 || error "kubectl is required but not installed"
    command -v helm >/dev/null 2>&1 || error "Helm is required but not installed"
    
    log "All prerequisites satisfied"
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    # Build API image
    docker build -f Dockerfile -t sovereign-grid/api:${TIMESTAMP} -t sovereign-grid/api:latest .
    if [ $? -ne 0 ]; then
        error "Failed to build API image"
    fi
    
    # Build Worker image
    docker build -f Dockerfile.worker -t sovereign-grid/worker:${TIMESTAMP} -t sovereign-grid/worker:latest .
    if [ $? -ne 0 ]; then
        error "Failed to build Worker image"
    fi
    
    log "Docker images built successfully"
}

# Push images to registry
push_images() {
    log "Pushing images to container registry..."
    
    # Tag for registry
    REGISTRY="ghcr.io/sovereign-grid"
    
    docker tag sovereign-grid/api:latest ${REGISTRY}/api:${TIMESTAMP}
    docker tag sovereign-grid/api:latest ${REGISTRY}/api:latest
    docker tag sovereign-grid/worker:latest ${REGISTRY}/worker:${TIMESTAMP}
    docker tag sovereign-grid/worker:latest ${REGISTRY}/worker:latest
    
    docker push ${REGISTRY}/api:${TIMESTAMP}
    docker push ${REGISTRY}/api:latest
    docker push ${REGISTRY}/worker:${TIMESTAMP}
    docker push ${REGISTRY}/worker:latest
    
    log "Images pushed successfully"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    docker run --rm \
        -e SUPABASE_URL="${SUPABASE_URL}" \
        -e SUPABASE_KEY="${SUPABASE_KEY}" \
        sovereign-grid/api:${TIMESTAMP} \
        python scripts/migrate.py
    
    if [ $? -ne 0 ]; then
        error "Database migrations failed"
    fi
    
    log "Migrations completed successfully"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log "Deploying to Kubernetes cluster..."
    
    # Apply namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Apply secrets
    kubectl apply -f k8s/secret.yaml
    
    # Apply configmaps
    kubectl apply -f k8s/configmap.yaml
    
    # Update deployment with new image tag
    sed -i "s|image: sovereign-grid/api:.*|image: ghcr.io/sovereign-grid/api:${TIMESTAMP}|g" k8s/deployment.yaml
    sed -i "s|image: sovereign-grid/worker:.*|image: ghcr.io/sovereign-grid/worker:${TIMESTAMP}|g" k8s/deployment.yaml
    
    # Apply deployments
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/ingress.yaml
    kubectl apply -f k8s/hpa.yaml
    
    # Wait for rollout
    kubectl rollout status deployment/sovereign-api -n sovereign-grid --timeout=300s
    
    log "Kubernetes deployment completed"
}

# Run smoke tests
run_smoke_tests() {
    log "Running smoke tests..."
    
    # Wait for service to be ready
    sleep 30
    
    # Test health endpoint
    curl -f https://api.sovereigngrid.com/health || error "Health check failed"
    
    # Test API endpoint
    curl -f -X POST https://api.sovereigngrid.com/v1/sovereign/execute \
        -H "Content-Type: application/json" \
        -H "X-Sovereign-Key: ${TEST_API_KEY}" \
        -d '{"user_id":"test","execution_mode":"fact_check","text_payload":"Test"}' || error "API test failed"
    
    log "Smoke tests passed"
}

# Send deployment notification
send_notification() {
    log "Sending deployment notification..."
    
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Sovereign Grid v${TIMESTAMP} deployed to ${ENVIRONMENT}\"}" \
        "${SLACK_WEBHOOK_URL}" || warn "Failed to send Slack notification"
}

# Main deployment function
main() {
    log "Starting deployment to ${ENVIRONMENT} environment"
    
    check_prerequisites
    build_images
    push_images
    run_migrations
    deploy_kubernetes
    run_smoke_tests
    send_notification
    
    log "Deployment completed successfully!"
}

# Run main function
main "$@"
