# True-Asset-ALLUSE Deployment Automation

**Autopilot for Wealth.....Engineered for compounding income and corpus**

This directory contains all the necessary automation scripts, configurations, and documentation for deploying the True-Asset-ALLUSE wealth management autopilot system to AWS in a production environment.

## 🚀 One-Click Deployment

For a complete automated deployment, simply run:

```bash
./deployment/scripts/deploy.sh
```

This script will:
- ✅ Check all prerequisites
- ✅ Deploy AWS infrastructure with Terraform
- ✅ Build and push Docker images to ECR
- ✅ Configure kubectl for EKS
- ✅ Deploy Kubernetes resources
- ✅ Install applications with Helm
- ✅ Configure SSL certificates
- ✅ Set up monitoring and logging
- ✅ Run comprehensive health checks

## 📋 Prerequisites

Before running the deployment script, ensure you have:

### Required Tools
- **AWS CLI** (v2.0+) - `aws --version`
- **kubectl** (v1.27+) - `kubectl version --client`
- **Helm** (v3.0+) - `helm version`
- **Terraform** (v1.0+) - `terraform version`
- **Docker** (v20.0+) - `docker --version`

### AWS Configuration
```bash
# Configure AWS credentials
aws configure

# Verify access
aws sts get-caller-identity
```

### Required AWS Permissions
Your AWS user/role needs permissions for:
- EC2 (VPC, Subnets, Security Groups)
- EKS (Cluster, Node Groups)
- RDS (PostgreSQL instances)
- ElastiCache (Redis clusters)
- ECR (Container registry)
- IAM (Roles and policies)
- Route53 (DNS management)
- Certificate Manager (SSL certificates)

## 🏗️ Infrastructure Components

The deployment creates the following AWS resources:

### Networking
- **VPC** with public and private subnets across 2 AZs
- **Internet Gateway** for public internet access
- **NAT Gateways** for private subnet internet access
- **Route Tables** with appropriate routing rules

### Compute
- **EKS Cluster** (v1.27) with managed node groups
- **EC2 instances** (t3.large) for worker nodes
- **Auto Scaling Groups** for dynamic scaling

### Storage & Databases
- **RDS PostgreSQL** (15.3) with Multi-AZ deployment
- **ElastiCache Redis** cluster for caching
- **EBS volumes** for persistent storage

### Security
- **Security Groups** with least-privilege access
- **IAM Roles** for service authentication
- **VPC Flow Logs** for network monitoring

### Container Registry
- **ECR Repository** for Docker images

## 🐳 Docker Images

The system builds the following Docker images:

### Main Application
- **Dockerfile.main** - Complete application with all workstreams
- **Multi-stage build** for optimized image size
- **Non-root user** for security
- **Health checks** built-in

### Workstream-Specific Images (Optional)
- **ws1-rules-engine** - Rules Engine & Constitution Framework
- **ws2-protocol-engine** - Protocol Engine & Risk Management
- **ws3-account-management** - Account Management & Forking
- **ws4-market-data-execution** - Market Data & Execution
- **ws5-portfolio-management** - Portfolio Management & Analytics
- **ws6-user-interface** - User Interface & API Layer

## ☸️ Kubernetes Deployment

### Namespace Organization
```
true-asset-alluse/          # Main application namespace
├── deployments/            # Application deployments
├── services/              # Service definitions
├── configmaps/            # Configuration data
├── secrets/               # Sensitive data
└── ingress/               # External access

ingress-nginx/             # Ingress controller
monitoring/                # Prometheus & Grafana
cert-manager/              # SSL certificate management
```

### Resource Allocation
- **CPU**: 1-2 cores per pod
- **Memory**: 2-4 GB per pod
- **Replicas**: 3-10 (auto-scaling enabled)
- **Storage**: 10 GB persistent volumes

## 📊 Monitoring & Observability

### Prometheus Stack
- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization dashboards
- **AlertManager** - Alert routing and management

### Logging
- **Fluentd** - Log collection and forwarding
- **CloudWatch Logs** - Centralized log storage
- **Log aggregation** across all pods

### Health Checks
- **Liveness probes** - Container health
- **Readiness probes** - Service availability
- **Custom health endpoints** - Application-specific checks

## 🔒 Security Features

### Network Security
- **Private subnets** for application workloads
- **Security groups** with minimal required access
- **VPC Flow Logs** for network monitoring

### Application Security
- **Non-root containers** for reduced attack surface
- **Read-only root filesystem** where possible
- **Resource limits** to prevent resource exhaustion
- **Pod Security Standards** enforcement

### Data Security
- **Encryption at rest** for RDS and EBS
- **Encryption in transit** with TLS/SSL
- **Secrets management** with Kubernetes secrets
- **Regular security scanning** with Trivy

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow
```
Pull Request → Test → Security Scan
Push to develop → Test → Build → Deploy to Staging
Push to main → Test → Build → Deploy to Production
```

### Automated Testing
- **Unit tests** with pytest
- **Integration tests** with real services
- **Security scanning** with Trivy
- **Code quality** with flake8, mypy, bandit

### Deployment Stages
1. **Build** - Docker images built and pushed to ECR
2. **Deploy** - Helm charts deployed to Kubernetes
3. **Test** - Health checks and integration tests
4. **Monitor** - Continuous monitoring and alerting

## 🛠️ Operational Procedures

### Deployment Commands

#### Full Deployment
```bash
./deployment/scripts/deploy.sh
```

#### Partial Deployment Options
```bash
# Skip infrastructure (use existing)
./deployment/scripts/deploy.sh --skip-infra

# Skip Docker build (use existing images)
./deployment/scripts/deploy.sh --skip-build

# Skip tests (faster deployment)
./deployment/scripts/deploy.sh --skip-tests

# Deploy to different environment
./deployment/scripts/deploy.sh --environment staging

# Deploy to different region
./deployment/scripts/deploy.sh --region us-west-2
```

### Health Checks
```bash
# Run comprehensive health checks
./deployment/scripts/health-check.sh

# Check specific components
kubectl get pods -n true-asset-alluse
kubectl get svc -n true-asset-alluse
kubectl logs -f deployment/true-asset-alluse -n true-asset-alluse
```

### Scaling Operations
```bash
# Manual scaling
kubectl scale deployment true-asset-alluse --replicas=5 -n true-asset-alluse

# Check auto-scaling status
kubectl get hpa -n true-asset-alluse

# Update resource limits
helm upgrade true-asset-alluse deployment/helm-charts/true-asset-alluse \
  --set resources.requests.cpu=2000m \
  --set resources.requests.memory=4Gi
```

### Backup & Recovery
```bash
# Database backup
kubectl exec -it <postgres-pod> -n true-asset-alluse -- pg_dump -U postgres trueassetalluse > backup.sql

# Restore database
kubectl exec -i <postgres-pod> -n true-asset-alluse -- psql -U postgres trueassetalluse < backup.sql

# Helm rollback
helm rollback true-asset-alluse -n true-asset-alluse
```

## 🔧 Configuration Management

### Environment Variables
Key configuration is managed through:
- **Kubernetes ConfigMaps** - Non-sensitive configuration
- **Kubernetes Secrets** - Sensitive data (passwords, API keys)
- **Helm values** - Deployment-specific settings

### Important Settings
```yaml
# Database configuration
DATABASE_HOST: <rds-endpoint>
DATABASE_NAME: trueassetalluse
DATABASE_USER: postgres

# Redis configuration
REDIS_HOST: <elasticache-endpoint>
REDIS_PORT: 6379

# Application settings
ENVIRONMENT: production
LOG_LEVEL: INFO
CONSTITUTION_VERSION: "1.3"
```

## 📈 Performance Optimization

### Resource Tuning
- **CPU requests/limits** based on workload patterns
- **Memory requests/limits** to prevent OOM kills
- **JVM tuning** for optimal garbage collection
- **Database connection pooling** for efficiency

### Scaling Configuration
- **Horizontal Pod Autoscaler** based on CPU/memory
- **Vertical Pod Autoscaler** for right-sizing
- **Cluster Autoscaler** for node scaling
- **Database read replicas** for read scaling

## 🚨 Troubleshooting

### Common Issues

#### Pod Startup Issues
```bash
# Check pod status
kubectl describe pod <pod-name> -n true-asset-alluse

# Check logs
kubectl logs <pod-name> -n true-asset-alluse --previous

# Check events
kubectl get events -n true-asset-alluse --sort-by='.lastTimestamp'
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it <app-pod> -n true-asset-alluse -- nc -zv <db-host> 5432

# Check database logs
aws rds describe-db-log-files --db-instance-identifier <db-instance>
```

#### Ingress/Load Balancer Issues
```bash
# Check ingress status
kubectl describe ingress -n true-asset-alluse

# Check load balancer
kubectl get svc -n ingress-nginx

# Check DNS resolution
nslookup <your-domain>
```

### Support Contacts
- **Infrastructure Issues**: DevOps Team
- **Application Issues**: Development Team
- **Security Issues**: Security Team

## 📚 Additional Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/)

## 🎯 Next Steps

After successful deployment:

1. **Configure DNS** - Point your domain to the LoadBalancer
2. **Set up monitoring alerts** - Configure Prometheus alerting rules
3. **Enable backups** - Set up automated database backups
4. **Security hardening** - Review and implement additional security measures
5. **Performance testing** - Run load tests to validate performance
6. **Documentation** - Update operational runbooks

---

**Need Help?** Check the troubleshooting section or contact the development team.

