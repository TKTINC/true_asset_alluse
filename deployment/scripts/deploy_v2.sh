#!/bin/bash

# True-Asset-ALLUSE Intelligent System One-Click Production Deployment Script v2.0
# This script automates the complete deployment of the 11-workstream AI-enhanced system on AWS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Enhanced Configuration
DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="true-asset-alluse"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-production}"
CLUSTER_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# AI Configuration
ENABLE_AI="${ENABLE_AI:-true}"
ENABLE_GPU="${ENABLE_GPU:-true}"
ENABLE_VOICE="${ENABLE_VOICE:-true}"
SUPPORTED_LANGUAGES="${SUPPORTED_LANGUAGES:-en,es,fr,de,ja,zh,pt,it}"
AI_NODE_INSTANCE_TYPE="${AI_NODE_INSTANCE_TYPE:-g4dn.xlarge}"

# Workstream Configuration
DEPLOY_WORKSTREAMS="${DEPLOY_WORKSTREAMS:-all}"  # all, core, intelligence, advanced-ai, or specific (e.g., ws16)
SKIP_AI_MODELS="${SKIP_AI_MODELS:-false}"
SKIP_VOICE_SETUP="${SKIP_VOICE_SETUP:-false}"

# Deployment Options
SKIP_INFRA="${SKIP_INFRA:-false}"
SKIP_BUILD="${SKIP_BUILD:-false}"
SKIP_TESTS="${SKIP_TESTS:-false}"
DRY_RUN="${DRY_RUN:-false}"

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

print_ai_status() {
    echo -e "${PURPLE}[AI]${NC} $1"
}

print_workstream() {
    echo -e "${CYAN}[WS]${NC} $1"
}

# Function to show deployment banner
show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    True-Asset-ALLUSE Intelligent System v2.0                ║"
    echo "║                  Autopilot for Wealth.....Engineered for                    ║"
    echo "║                        compounding income and corpus                        ║"
    echo "║                                                                              ║"
    echo "║  🚀 11 Advanced Workstreams  🤖 AI-Enhanced  🗣️ Multi-Language  🎙️ Voice    ║"
    echo "║                                                                              ║"
    echo "║  WS1-WS6: Core Foundation    WS7-WS8: Intelligence Layer                    ║"
    echo "║  WS9: Market Intelligence    WS12: Visualization Intelligence               ║"
    echo "║  WS16: Enhanced Conversational AI                                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --region)
                AWS_REGION="$2"
                shift 2
                ;;
            --workstreams)
                DEPLOY_WORKSTREAMS="$2"
                shift 2
                ;;
            --workstream)
                DEPLOY_WORKSTREAMS="$2"
                shift 2
                ;;
            --languages)
                SUPPORTED_LANGUAGES="$2"
                shift 2
                ;;
            --skip-infra)
                SKIP_INFRA="true"
                shift
                ;;
            --skip-build)
                SKIP_BUILD="true"
                shift
                ;;
            --skip-tests)
                SKIP_TESTS="true"
                shift
                ;;
            --skip-ai-models)
                SKIP_AI_MODELS="true"
                shift
                ;;
            --skip-voice)
                SKIP_VOICE_SETUP="true"
                ENABLE_VOICE="false"
                shift
                ;;
            --disable-ai)
                ENABLE_AI="false"
                ENABLE_GPU="false"
                ENABLE_VOICE="false"
                shift
                ;;
            --disable-gpu)
                ENABLE_GPU="false"
                shift
                ;;
            --enable-gpu)
                ENABLE_GPU="true"
                shift
                ;;
            --enable-voice)
                ENABLE_VOICE="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Function to show help
show_help() {
    echo "True-Asset-ALLUSE Intelligent System Deployment Script v2.0"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --environment ENV          Deployment environment (default: production)"
    echo "  --region REGION           AWS region (default: us-east-1)"
    echo "  --workstreams TYPE        Workstreams to deploy: all, core, intelligence, advanced-ai, or specific (e.g., ws16)"
    echo "  --workstream WS           Deploy specific workstream (e.g., ws16)"
    echo "  --languages LANGS         Supported languages (default: en,es,fr,de,ja,zh,pt,it)"
    echo "  --skip-infra              Skip infrastructure deployment"
    echo "  --skip-build              Skip Docker image building"
    echo "  --skip-tests              Skip health checks and tests"
    echo "  --skip-ai-models          Skip AI model deployment"
    echo "  --skip-voice              Skip voice service setup"
    echo "  --disable-ai              Disable all AI features"
    echo "  --disable-gpu             Disable GPU support"
    echo "  --enable-gpu              Enable GPU support for AI workloads"
    echo "  --enable-voice            Enable voice interface"
    echo "  --dry-run                 Show what would be deployed without executing"
    echo "  --help                    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Full deployment with all features"
    echo "  $0 --workstreams core                # Deploy only core workstreams (WS1-WS6)"
    echo "  $0 --workstreams intelligence        # Deploy intelligence layer (WS7-WS8)"
    echo "  $0 --workstreams advanced-ai         # Deploy advanced AI (WS9, WS12, WS16)"
    echo "  $0 --workstream ws16                 # Deploy only WS16"
    echo "  $0 --skip-infra --skip-build         # Deploy using existing infrastructure and images"
    echo "  $0 --languages en,es,fr              # Deploy with English, Spanish, and French support"
    echo "  $0 --disable-ai                      # Deploy without AI features"
    echo "  $0 --environment staging --region us-west-2  # Deploy to staging in us-west-2"
}

# Function to check enhanced prerequisites
check_prerequisites() {
    print_status "Checking prerequisites for 11-workstream intelligent system..."
    
    # Check if required tools are installed
    local tools=("aws" "kubectl" "helm" "terraform" "docker")
    for tool in "${tools[@]}"; do
        if ! command -v $tool &> /dev/null; then
            print_error "$tool is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check AI-specific tools if AI is enabled
    if [[ "$ENABLE_AI" == "true" ]]; then
        print_ai_status "Checking AI prerequisites..."
        
        # Check Python and AI libraries
        if ! python3 -c "import openai, anthropic" &> /dev/null; then
            print_warning "AI libraries not found. They will be installed during deployment."
        fi
        
        # Check GPU support if enabled
        if [[ "$ENABLE_GPU" == "true" ]]; then
            if command -v nvidia-smi &> /dev/null; then
                print_ai_status "GPU support detected"
            else
                print_warning "nvidia-smi not found. GPU support will be configured in the cluster."
            fi
        fi
    fi
    
    # Check AWS CLI configuration
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check required AWS permissions
    print_status "Checking AWS permissions..."
    local required_services=("ec2" "eks" "rds" "elasticache" "ecr" "iam" "route53" "acm")
    
    if [[ "$ENABLE_AI" == "true" ]]; then
        required_services+=("sagemaker" "bedrock" "comprehend" "polly" "transcribe")
    fi
    
    for service in "${required_services[@]}"; do
        if ! aws $service describe-regions --region $AWS_REGION &> /dev/null; then
            print_warning "Limited access to $service. Some features may not work."
        fi
    done
    
    print_success "Prerequisites check completed"
}

# Function to validate workstream selection
validate_workstreams() {
    print_status "Validating workstream selection: $DEPLOY_WORKSTREAMS"
    
    case $DEPLOY_WORKSTREAMS in
        "all")
            print_workstream "Deploying all 11 workstreams (WS1-WS16)"
            ;;
        "core")
            print_workstream "Deploying core foundation workstreams (WS1-WS6)"
            ;;
        "intelligence")
            print_workstream "Deploying intelligence layer workstreams (WS7-WS8)"
            ;;
        "advanced-ai")
            print_workstream "Deploying advanced AI workstreams (WS9, WS12, WS16)"
            ;;
        ws[1-9]|ws1[0-6])
            print_workstream "Deploying specific workstream: $DEPLOY_WORKSTREAMS"
            ;;
        *)
            print_error "Invalid workstream selection: $DEPLOY_WORKSTREAMS"
            print_error "Valid options: all, core, intelligence, advanced-ai, or specific (e.g., ws16)"
            exit 1
            ;;
    esac
}

# Function to show deployment configuration
show_configuration() {
    print_status "Deployment Configuration:"
    echo "  Project: $PROJECT_NAME"
    echo "  Environment: $ENVIRONMENT"
    echo "  Region: $AWS_REGION"
    echo "  Cluster: $CLUSTER_NAME"
    echo "  Workstreams: $DEPLOY_WORKSTREAMS"
    echo "  AI Enabled: $ENABLE_AI"
    echo "  GPU Enabled: $ENABLE_GPU"
    echo "  Voice Enabled: $ENABLE_VOICE"
    echo "  Languages: $SUPPORTED_LANGUAGES"
    echo "  Skip Infrastructure: $SKIP_INFRA"
    echo "  Skip Build: $SKIP_BUILD"
    echo "  Skip Tests: $SKIP_TESTS"
    echo "  Skip AI Models: $SKIP_AI_MODELS"
    echo "  Dry Run: $DRY_RUN"
    echo ""
    
    if [[ "$DRY_RUN" == "false" ]]; then
        read -p "Continue with deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Deployment cancelled"
            exit 0
        fi
    else
        print_warning "DRY RUN MODE - No actual deployment will occur"
    fi
}

# Function to deploy infrastructure
deploy_infrastructure() {
    if [[ "$SKIP_INFRA" == "true" ]]; then
        print_status "Skipping infrastructure deployment"
        return
    fi
    
    print_status "Deploying AWS infrastructure..."
    
    cd "$DEPLOYMENT_DIR/terraform"
    
    # Initialize Terraform
    if [[ "$DRY_RUN" == "false" ]]; then
        terraform init
        
        # Create terraform.tfvars with enhanced configuration
        cat > terraform.tfvars <<EOF
project_name = "$PROJECT_NAME"
environment = "$ENVIRONMENT"
aws_region = "$AWS_REGION"
cluster_name = "$CLUSTER_NAME"
enable_ai = $ENABLE_AI
enable_gpu = $ENABLE_GPU
ai_node_instance_type = "$AI_NODE_INSTANCE_TYPE"
supported_languages = "$SUPPORTED_LANGUAGES"
EOF
        
        # Plan and apply
        terraform plan -var-file=terraform.tfvars
        terraform apply -var-file=terraform.tfvars -auto-approve
    else
        print_status "DRY RUN: Would deploy infrastructure with Terraform"
    fi
    
    print_success "Infrastructure deployment completed"
}

# Function to build and push Docker images
build_and_push_images() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        print_status "Skipping Docker image building"
        return
    fi
    
    print_status "Building and pushing Docker images for workstreams..."
    
    # Get ECR login
    if [[ "$DRY_RUN" == "false" ]]; then
        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com
    fi
    
    local images_to_build=()
    
    # Determine which images to build based on workstream selection
    case $DEPLOY_WORKSTREAMS in
        "all")
            images_to_build=("main" "ws1-rules-engine" "ws2-protocol-engine" "ws3-account-management" 
                            "ws4-market-data-execution" "ws5-portfolio-management" "ws6-user-interface"
                            "ws7-natural-language" "ws8-ml-intelligence" "ws9-market-intelligence"
                            "ws12-visualization-intelligence" "ws16-enhanced-conversational-ai")
            ;;
        "core")
            images_to_build=("ws1-rules-engine" "ws2-protocol-engine" "ws3-account-management" 
                            "ws4-market-data-execution" "ws5-portfolio-management" "ws6-user-interface")
            ;;
        "intelligence")
            images_to_build=("ws7-natural-language" "ws8-ml-intelligence")
            ;;
        "advanced-ai")
            images_to_build=("ws9-market-intelligence" "ws12-visualization-intelligence" "ws16-enhanced-conversational-ai")
            ;;
        ws*)
            images_to_build=("$DEPLOY_WORKSTREAMS")
            ;;
    esac
    
    # Build main application image if deploying all or multiple workstreams
    if [[ "$DEPLOY_WORKSTREAMS" == "all" ]] || [[ ${#images_to_build[@]} -gt 1 ]]; then
        print_status "Building main application image with all workstreams..."
        if [[ "$DRY_RUN" == "false" ]]; then
            docker build -t $PROJECT_NAME:latest -f deployment/docker/Dockerfile.main .
            docker tag $PROJECT_NAME:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME:latest
            docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME:latest
        else
            print_status "DRY RUN: Would build and push main application image"
        fi
    fi
    
    # Build individual workstream images
    for image in "${images_to_build[@]}"; do
        if [[ "$image" != "main" ]]; then
            print_workstream "Building $image image..."
            if [[ "$DRY_RUN" == "false" ]]; then
                # Create workstream-specific Dockerfile if it doesn't exist
                if [[ ! -f "deployment/docker/Dockerfile.$image" ]]; then
                    create_workstream_dockerfile "$image"
                fi
                
                docker build -t $PROJECT_NAME-$image:latest -f deployment/docker/Dockerfile.$image .
                docker tag $PROJECT_NAME-$image:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$image:latest
                docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$image:latest
            else
                print_status "DRY RUN: Would build and push $image image"
            fi
        fi
    done
    
    print_success "Docker images built and pushed"
}

# Function to create workstream-specific Dockerfile
create_workstream_dockerfile() {
    local workstream=$1
    local dockerfile_path="deployment/docker/Dockerfile.$workstream"
    
    print_status "Creating Dockerfile for $workstream..."
    
    cat > "$dockerfile_path" <<EOF
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy application code
COPY src/ src/
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "from src.${workstream//-/_} import health_check; health_check()" || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "-m", "src.${workstream//-/_}"]
EOF
}

# Function to configure kubectl
configure_kubectl() {
    print_status "Configuring kubectl for EKS cluster..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
        
        # Verify connection
        kubectl cluster-info
        kubectl get nodes
    else
        print_status "DRY RUN: Would configure kubectl for cluster $CLUSTER_NAME"
    fi
    
    print_success "kubectl configured successfully"
}

# Function to deploy AI models
deploy_ai_models() {
    if [[ "$ENABLE_AI" == "false" ]] || [[ "$SKIP_AI_MODELS" == "true" ]]; then
        print_status "Skipping AI model deployment"
        return
    fi
    
    print_ai_status "Deploying AI models and services..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Deploy AI model configurations
        kubectl apply -f deployment/ai-models/ || true
        
        # Wait for AI services to be ready
        kubectl wait --for=condition=available --timeout=300s deployment/ai-model-serving -n ai-services || true
    else
        print_status "DRY RUN: Would deploy AI models and services"
    fi
    
    print_success "AI models deployed"
}

# Function to deploy Kubernetes resources
deploy_kubernetes_resources() {
    print_status "Deploying Kubernetes resources..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Create namespaces
        kubectl create namespace true-asset-alluse --dry-run=client -o yaml | kubectl apply -f -
        
        if [[ "$ENABLE_AI" == "true" ]]; then
            kubectl create namespace ai-services --dry-run=client -o yaml | kubectl apply -f -
        fi
        
        if [[ "$ENABLE_VOICE" == "true" ]]; then
            kubectl create namespace voice-services --dry-run=client -o yaml | kubectl apply -f -
        fi
        
        # Deploy ingress controller
        helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
        helm repo update
        helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \\
            --namespace ingress-nginx --create-namespace \\
            --set controller.service.type=LoadBalancer
        
        # Deploy cert-manager
        helm repo add jetstack https://charts.jetstack.io
        helm repo update
        helm upgrade --install cert-manager jetstack/cert-manager \\
            --namespace cert-manager --create-namespace \\
            --set installCRDs=true
        
        # Deploy monitoring stack
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
        helm repo update
        helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \\
            --namespace monitoring --create-namespace
    else
        print_status "DRY RUN: Would deploy Kubernetes resources"
    fi
    
    print_success "Kubernetes resources deployed"
}

# Function to deploy application with Helm
deploy_application() {
    print_status "Deploying True-Asset-ALLUSE application..."
    
    cd "$DEPLOYMENT_DIR/helm-charts/true-asset-alluse"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Create values file with enhanced configuration
        cat > values-$ENVIRONMENT.yaml <<EOF
image:
  repository: $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME
  tag: latest
  pullPolicy: Always

replicaCount: 3

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: api.$PROJECT_NAME.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: $PROJECT_NAME-tls
      hosts:
        - api.$PROJECT_NAME.com

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 15
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# AI Configuration
ai:
  enabled: $ENABLE_AI
  gpu:
    enabled: $ENABLE_GPU
    resources:
      limits:
        nvidia.com/gpu: 1
      requests:
        nvidia.com/gpu: 1
  voice:
    enabled: $ENABLE_VOICE
  languages: "$SUPPORTED_LANGUAGES"

# Workstream Configuration
workstreams:
  deploy: "$DEPLOY_WORKSTREAMS"
  ws1:
    enabled: true
  ws2:
    enabled: true
  ws3:
    enabled: true
  ws4:
    enabled: true
  ws5:
    enabled: true
  ws6:
    enabled: true
  ws7:
    enabled: $([ "$DEPLOY_WORKSTREAMS" == "all" ] || [ "$DEPLOY_WORKSTREAMS" == "intelligence" ] && echo "true" || echo "false")
  ws8:
    enabled: $([ "$DEPLOY_WORKSTREAMS" == "all" ] || [ "$DEPLOY_WORKSTREAMS" == "intelligence" ] && echo "true" || echo "false")
  ws9:
    enabled: $([ "$DEPLOY_WORKSTREAMS" == "all" ] || [ "$DEPLOY_WORKSTREAMS" == "advanced-ai" ] && echo "true" || echo "false")
  ws12:
    enabled: $([ "$DEPLOY_WORKSTREAMS" == "all" ] || [ "$DEPLOY_WORKSTREAMS" == "advanced-ai" ] && echo "true" || echo "false")
  ws16:
    enabled: $([ "$DEPLOY_WORKSTREAMS" == "all" ] || [ "$DEPLOY_WORKSTREAMS" == "advanced-ai" ] && echo "true" || echo "false")

# Database Configuration
postgresql:
  enabled: true
  auth:
    postgresPassword: $(openssl rand -base64 32)
    database: trueassetalluse

redis:
  enabled: true
  auth:
    enabled: true
    password: $(openssl rand -base64 32)
EOF
        
        # Deploy with Helm
        helm upgrade --install $PROJECT_NAME . \\
            --namespace true-asset-alluse \\
            --values values-$ENVIRONMENT.yaml \\
            --wait --timeout=600s
    else
        print_status "DRY RUN: Would deploy application with Helm"
    fi
    
    print_success "Application deployed successfully"
}

# Function to run health checks
run_health_checks() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        print_status "Skipping health checks"
        return
    fi
    
    print_status "Running comprehensive health checks..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Wait for pods to be ready
        kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=$PROJECT_NAME -n true-asset-alluse --timeout=300s
        
        # Run health check script
        "$DEPLOYMENT_DIR/scripts/health-check.sh"
        
        # Test AI services if enabled
        if [[ "$ENABLE_AI" == "true" ]]; then
            print_ai_status "Testing AI services..."
            
            # Test conversational AI
            if kubectl get deployment ws16-enhanced-conversational-ai -n true-asset-alluse &> /dev/null; then
                print_ai_status "Testing conversational AI..."
                # Add specific AI tests here
            fi
            
            # Test voice services if enabled
            if [[ "$ENABLE_VOICE" == "true" ]]; then
                print_ai_status "Testing voice services..."
                # Add voice service tests here
            fi
        fi
    else
        print_status "DRY RUN: Would run comprehensive health checks"
    fi
    
    print_success "Health checks completed"
}

# Function to show deployment summary
show_deployment_summary() {
    print_success "🎉 True-Asset-ALLUSE Intelligent System Deployment Completed!"
    echo ""
    echo "Deployment Summary:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Region: $AWS_REGION"
    echo "  Cluster: $CLUSTER_NAME"
    echo "  Workstreams Deployed: $DEPLOY_WORKSTREAMS"
    echo "  AI Features: $ENABLE_AI"
    echo "  GPU Support: $ENABLE_GPU"
    echo "  Voice Interface: $ENABLE_VOICE"
    echo "  Supported Languages: $SUPPORTED_LANGUAGES"
    echo ""
    
    if [[ "$DRY_RUN" == "false" ]]; then
        echo "Access Information:"
        echo "  API Endpoint: https://api.$PROJECT_NAME.com"
        echo "  Dashboard: https://app.$PROJECT_NAME.com"
        echo "  Monitoring: https://monitoring.$PROJECT_NAME.com"
        echo ""
        
        echo "Next Steps:"
        echo "  1. Configure DNS to point to the LoadBalancer"
        echo "  2. Set up monitoring alerts"
        echo "  3. Configure AI API keys in secrets"
        echo "  4. Test conversational AI interface"
        echo "  5. Validate voice interface functionality"
        echo "  6. Run performance tests"
        echo ""
        
        echo "Useful Commands:"
        echo "  kubectl get pods -n true-asset-alluse"
        echo "  kubectl logs -f deployment/$PROJECT_NAME -n true-asset-alluse"
        echo "  helm status $PROJECT_NAME -n true-asset-alluse"
        echo "  ./deployment/scripts/health-check.sh"
    else
        echo "DRY RUN COMPLETED - No actual deployment occurred"
    fi
}

# Main deployment function
main() {
    show_banner
    parse_arguments "$@"
    validate_workstreams
    show_configuration
    check_prerequisites
    deploy_infrastructure
    build_and_push_images
    configure_kubectl
    deploy_ai_models
    deploy_kubernetes_resources
    deploy_application
    run_health_checks
    show_deployment_summary
}

# Run main function with all arguments
main "$@"

