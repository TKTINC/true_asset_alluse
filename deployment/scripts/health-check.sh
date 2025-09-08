#!/bin/bash

# True-Asset-ALLUSE Health Check Script
# This script performs comprehensive health checks on the deployed system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_NAME="true-asset-alluse"
NAMESPACE="${PROJECT_NAME}"

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

# Function to check pod health
check_pods() {
    print_status "Checking pod health..."
    
    # Get pod status
    local pods=$(kubectl get pods -n ${NAMESPACE} -o jsonpath='{.items[*].metadata.name}')
    local failed_pods=0
    
    for pod in $pods; do
        local status=$(kubectl get pod $pod -n ${NAMESPACE} -o jsonpath='{.status.phase}')
        local ready=$(kubectl get pod $pod -n ${NAMESPACE} -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
        
        if [[ "$status" == "Running" && "$ready" == "True" ]]; then
            print_success "Pod $pod is healthy"
        else
            print_error "Pod $pod is not healthy (Status: $status, Ready: $ready)"
            failed_pods=$((failed_pods + 1))
        fi
    done
    
    if [[ $failed_pods -eq 0 ]]; then
        print_success "All pods are healthy!"
    else
        print_error "$failed_pods pods are not healthy"
        return 1
    fi
}

# Function to check services
check_services() {
    print_status "Checking service health..."
    
    local services=$(kubectl get svc -n ${NAMESPACE} -o jsonpath='{.items[*].metadata.name}')
    
    for service in $services; do
        local endpoints=$(kubectl get endpoints $service -n ${NAMESPACE} -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
        
        if [[ $endpoints -gt 0 ]]; then
            print_success "Service $service has $endpoints endpoints"
        else
            print_error "Service $service has no endpoints"
            return 1
        fi
    done
    
    print_success "All services are healthy!"
}

# Function to check application health endpoints
check_application_health() {
    print_status "Checking application health endpoints..."
    
    # Port forward to access the application
    kubectl port-forward svc/${PROJECT_NAME} 8080:80 -n ${NAMESPACE} &
    local port_forward_pid=$!
    
    # Wait for port forward to be ready
    sleep 5
    
    # Check health endpoint
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        print_success "Health endpoint is responding"
    else
        print_error "Health endpoint is not responding"
        kill $port_forward_pid
        return 1
    fi
    
    # Check readiness endpoint
    if curl -f http://localhost:8080/ready > /dev/null 2>&1; then
        print_success "Readiness endpoint is responding"
    else
        print_error "Readiness endpoint is not responding"
        kill $port_forward_pid
        return 1
    fi
    
    # Check metrics endpoint
    if curl -f http://localhost:8080/metrics > /dev/null 2>&1; then
        print_success "Metrics endpoint is responding"
    else
        print_warning "Metrics endpoint is not responding"
    fi
    
    # Clean up port forward
    kill $port_forward_pid
    
    print_success "Application health checks passed!"
}

# Function to check database connectivity
check_database() {
    print_status "Checking database connectivity..."
    
    # Get database pod
    local db_pod=$(kubectl get pods -n ${NAMESPACE} -l app=postgresql -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -n "$db_pod" ]]; then
        # Test database connection
        if kubectl exec $db_pod -n ${NAMESPACE} -- pg_isready > /dev/null 2>&1; then
            print_success "Database is accessible"
        else
            print_error "Database is not accessible"
            return 1
        fi
    else
        print_warning "Database pod not found (using external database)"
    fi
}

# Function to check Redis connectivity
check_redis() {
    print_status "Checking Redis connectivity..."
    
    # Get Redis pod
    local redis_pod=$(kubectl get pods -n ${NAMESPACE} -l app=redis -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -n "$redis_pod" ]]; then
        # Test Redis connection
        if kubectl exec $redis_pod -n ${NAMESPACE} -- redis-cli ping | grep -q PONG; then
            print_success "Redis is accessible"
        else
            print_error "Redis is not accessible"
            return 1
        fi
    else
        print_warning "Redis pod not found (using external Redis)"
    fi
}

# Function to check ingress
check_ingress() {
    print_status "Checking ingress configuration..."
    
    local ingress=$(kubectl get ingress -n ${NAMESPACE} -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -n "$ingress" ]]; then
        local hosts=$(kubectl get ingress $ingress -n ${NAMESPACE} -o jsonpath='{.spec.rules[*].host}')
        print_success "Ingress configured for hosts: $hosts"
        
        # Check if LoadBalancer has external IP
        local lb_ip=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
        if [[ -n "$lb_ip" ]]; then
            print_success "LoadBalancer external IP: $lb_ip"
        else
            print_warning "LoadBalancer external IP not yet assigned"
        fi
    else
        print_error "No ingress found"
        return 1
    fi
}

# Function to check monitoring
check_monitoring() {
    print_status "Checking monitoring stack..."
    
    # Check Prometheus
    local prometheus_pod=$(kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.name}')
    if [[ -n "$prometheus_pod" ]]; then
        print_success "Prometheus is running"
    else
        print_warning "Prometheus not found"
    fi
    
    # Check Grafana
    local grafana_pod=$(kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}')
    if [[ -n "$grafana_pod" ]]; then
        print_success "Grafana is running"
    else
        print_warning "Grafana not found"
    fi
}

# Main health check function
main() {
    echo "========================================"
    echo "True-Asset-ALLUSE Health Check"
    echo "========================================"
    echo ""
    
    local failed_checks=0
    
    # Run all health checks
    check_pods || failed_checks=$((failed_checks + 1))
    echo ""
    
    check_services || failed_checks=$((failed_checks + 1))
    echo ""
    
    check_application_health || failed_checks=$((failed_checks + 1))
    echo ""
    
    check_database || failed_checks=$((failed_checks + 1))
    echo ""
    
    check_redis || failed_checks=$((failed_checks + 1))
    echo ""
    
    check_ingress || failed_checks=$((failed_checks + 1))
    echo ""
    
    check_monitoring || failed_checks=$((failed_checks + 1))
    echo ""
    
    # Summary
    if [[ $failed_checks -eq 0 ]]; then
        print_success "All health checks passed! 🎉"
        exit 0
    else
        print_error "$failed_checks health checks failed"
        exit 1
    fi
}

# Run main function
main "$@"

