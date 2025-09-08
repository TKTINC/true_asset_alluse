#!/bin/bash

# True-Asset-ALLUSE One-Click Production Deployment Script
# This script automates the complete deployment of the True-Asset-ALLUSE system on AWS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="true-asset-alluse"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-production}"
CLUSTER_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if required tools are installed
    local tools=("aws" "kubectl" "helm" "terraform" "docker")
    for tool in "${tools[@]}"; do
        if ! command -v $tool &> /dev/null; then
            print_error "$tool is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying AWS infrastructure with Terraform..."
    
    cd "${DEPLOYMENT_DIR}/terraform"
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan -var="cluster_name=${CLUSTER_NAME}" -var="aws_region=${AWS_REGION}" -out=tfplan
    
    # Apply deployment
    terraform apply tfplan
    
    # Get outputs
    export VPC_ID=$(terraform output -raw vpc_id)
    export EKS_CLUSTER_NAME=$(terraform output -raw eks_cluster_name)
    export RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
    export REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
    export ECR_REPOSITORY_URL=$(terraform output -raw ecr_repository_url)
    
    print_success "Infrastructure deployed successfully!"
}

# Function to build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    # Get ECR login token
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPOSITORY_URL}
    
    # Build images for each workstream
    local workstreams=("ws1-rules-engine" "ws2-protocol-engine" "ws3-account-management" "ws4-market-data-execution" "ws5-portfolio-management" "ws6-user-interface")
    
    for ws in "${workstreams[@]}"; do
        print_status "Building ${ws} image..."
        docker build -f "${DEPLOYMENT_DIR}/docker/Dockerfile.${ws}" -t "${ECR_REPOSITORY_URL}:${ws}-latest" .
        docker push "${ECR_REPOSITORY_URL}:${ws}-latest"
        print_success "${ws} image built and pushed!"
    done
    
    # Build main application image
    print_status "Building main application image..."
    docker build -f "${DEPLOYMENT_DIR}/docker/Dockerfile.main" -t "${ECR_REPOSITORY_URL}:main-latest" .
    docker push "${ECR_REPOSITORY_URL}:main-latest"
    print_success "Main application image built and pushed!"
}

# Function to configure kubectl
configure_kubectl() {
    print_status "Configuring kubectl for EKS cluster..."
    
    aws eks update-kubeconfig --region ${AWS_REGION} --name ${EKS_CLUSTER_NAME}
    
    # Verify connection
    kubectl cluster-info
    
    print_success "kubectl configured successfully!"
}

# Function to deploy Kubernetes resources
deploy_kubernetes() {
    print_status "Deploying Kubernetes resources..."
    
    # Create namespace
    kubectl create namespace ${PROJECT_NAME} --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy secrets
    kubectl apply -f "${DEPLOYMENT_DIR}/kubernetes/secrets/" -n ${PROJECT_NAME}
    
    # Deploy ConfigMaps
    kubectl apply -f "${DEPLOYMENT_DIR}/kubernetes/configmaps/" -n ${PROJECT_NAME}
    
    # Deploy services
    kubectl apply -f "${DEPLOYMENT_DIR}/kubernetes/services/" -n ${PROJECT_NAME}
    
    # Deploy deployments
    kubectl apply -f "${DEPLOYMENT_DIR}/kubernetes/deployments/" -n ${PROJECT_NAME}
    
    # Deploy ingress
    kubectl apply -f "${DEPLOYMENT_DIR}/kubernetes/ingress/" -n ${PROJECT_NAME}
    
    print_success "Kubernetes resources deployed successfully!"
}

# Function to deploy with Helm
deploy_helm() {
    print_status "Deploying application with Helm..."
    
    # Add required Helm repositories
    helm repo add stable https://charts.helm.sh/stable
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Deploy NGINX Ingress Controller
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.service.type=LoadBalancer
    
    # Deploy Prometheus monitoring
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set grafana.adminPassword=admin123
    
    # Deploy True-Asset-ALLUSE application
    helm upgrade --install ${PROJECT_NAME} "${DEPLOYMENT_DIR}/helm-charts/${PROJECT_NAME}" \
        --namespace ${PROJECT_NAME} \
        --create-namespace \
        --set image.repository=${ECR_REPOSITORY_URL} \
        --set database.host=${RDS_ENDPOINT} \
        --set redis.host=${REDIS_ENDPOINT} \
        --set environment=${ENVIRONMENT}
    
    print_success "Helm deployment completed successfully!"
}

# Function to configure SSL certificates
configure_ssl() {
    print_status "Configuring SSL certificates..."
    
    # Install cert-manager
    kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.8.0/cert-manager.yaml
    
    # Wait for cert-manager to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s
    
    # Apply SSL certificate configuration
    kubectl apply -f "${DEPLOYMENT_DIR}/kubernetes/ssl/" -n ${PROJECT_NAME}
    
    print_success "SSL certificates configured successfully!"
}

# Function to configure monitoring and logging
configure_monitoring() {
    print_status "Configuring monitoring and logging..."
    
    # Deploy Fluentd for logging
    kubectl apply -f "${DEPLOYMENT_DIR}/kubernetes/logging/" -n ${PROJECT_NAME}
    
    # Configure Prometheus monitoring rules
    kubectl apply -f "${DEPLOYMENT_DIR}/kubernetes/monitoring/" -n ${PROJECT_NAME}
    
    print_success "Monitoring and logging configured successfully!"
}

# Function to run post-deployment tests
run_tests() {
    print_status "Running post-deployment tests..."
    
    # Wait for all pods to be ready
    kubectl wait --for=condition=ready pod -l app=${PROJECT_NAME} -n ${PROJECT_NAME} --timeout=600s
    
    # Run health checks
    "${DEPLOYMENT_DIR}/scripts/health-check.sh"
    
    # Run integration tests
    "${DEPLOYMENT_DIR}/scripts/integration-tests.sh"
    
    print_success "All tests passed successfully!"
}

# Function to display deployment information
display_info() {
    print_success "Deployment completed successfully!"
    echo ""
    echo "=== DEPLOYMENT INFORMATION ==="
    echo "Cluster Name: ${EKS_CLUSTER_NAME}"
    echo "Namespace: ${PROJECT_NAME}"
    echo "Region: ${AWS_REGION}"
    echo ""
    echo "=== ACCESS INFORMATION ==="
    
    # Get LoadBalancer URL
    local lb_url=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    echo "Application URL: https://${lb_url}"
    
    # Get Grafana URL
    local grafana_url=$(kubectl get svc -n monitoring prometheus-grafana -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    echo "Grafana URL: http://${grafana_url} (admin/admin123)"
    
    echo ""
    echo "=== USEFUL COMMANDS ==="
    echo "View pods: kubectl get pods -n ${PROJECT_NAME}"
    echo "View logs: kubectl logs -f deployment/${PROJECT_NAME} -n ${PROJECT_NAME}"
    echo "Port forward: kubectl port-forward svc/${PROJECT_NAME} 8080:80 -n ${PROJECT_NAME}"
    echo ""
}

# Main deployment function
main() {
    echo "========================================"
    echo "True-Asset-ALLUSE Production Deployment"
    echo "========================================"
    echo ""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-infra)
                SKIP_INFRA=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --region)
                AWS_REGION="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-infra     Skip infrastructure deployment"
                echo "  --skip-build     Skip Docker image building"
                echo "  --skip-tests     Skip post-deployment tests"
                echo "  --environment    Set environment (default: production)"
                echo "  --region         Set AWS region (default: us-east-1)"
                echo "  -h, --help       Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Start deployment
    print_status "Starting deployment to ${ENVIRONMENT} environment in ${AWS_REGION}..."
    
    check_prerequisites
    
    if [[ "${SKIP_INFRA}" != "true" ]]; then
        deploy_infrastructure
    fi
    
    if [[ "${SKIP_BUILD}" != "true" ]]; then
        build_and_push_images
    fi
    
    configure_kubectl
    deploy_kubernetes
    deploy_helm
    configure_ssl
    configure_monitoring
    
    if [[ "${SKIP_TESTS}" != "true" ]]; then
        run_tests
    fi
    
    display_info
    
    print_success "Deployment completed successfully! 🚀"
}

# Run main function
main "$@"

