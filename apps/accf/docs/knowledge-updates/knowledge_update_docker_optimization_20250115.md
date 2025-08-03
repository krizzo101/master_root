<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Knowledge Update: Docker Container Optimization (Generated 2025-01-15)","description":"This document provides an analysis of the current Docker container setup, identifies issues, proposes optimization opportunities, outlines best practices for 2025, and offers implementation guidance for Docker container optimization.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify its hierarchical structure and logical sections based on headings and content themes. Extract key elements such as code blocks, tables, lists, and important concepts that aid navigation and comprehension. Ensure all line numbers are accurate and sections do not overlap. Provide a clear, navigable JSON map with descriptive section names and element descriptions to facilitate efficient understanding and referencing of Docker container optimization strategies.","sections":[{"name":"Document Title","description":"Title of the knowledge update document indicating the focus on Docker container optimization and generation date.","line_start":7,"line_end":7},{"name":"Current State Analysis","description":"Analysis of the current Docker environment including image sizes, Dockerfile issues, and Docker Compose issues.","line_start":9,"line_end":43},{"name":"Docker Image Sizes","description":"Listing of Docker image sizes from previous builds highlighting size concerns.","line_start":11,"line_end":17},{"name":"Current Dockerfile Issues","description":"Detailed enumeration of problems found in the current Dockerfiles including base image, dependency management, build context, and runtime configuration issues.","line_start":18,"line_end":39},{"name":"Current Docker Compose Issues","description":"Issues identified in the current Docker Compose setup affecting service efficiency and resource management.","line_start":40,"line_end":43},{"name":"Optimization Opportunities","description":"Proposed strategies to optimize Docker builds and runtime including multi-stage builds, layer optimization, base image improvements, build context, and service-specific optimizations.","line_start":46,"line_end":71},{"name":"Best Practices for 2025","description":"Recommended best practices for Docker container optimization focusing on modern Python packaging, container security, build performance, and runtime efficiency.","line_start":73,"line_end":94},{"name":"Implementation Guidance","description":"Practical guidance on target image sizes and priority optimizations to implement for effective Docker container optimization.","line_start":96,"line_end":109}],"key_elements":[{"name":"Docker Image Sizes List","description":"A list of Docker images with their respective sizes indicating bloat issues, especially with the 'docker_flower' image.","line":12},{"name":"Base Image Problems","description":"Issues related to the choice and usage of base images in Dockerfiles including lack of multi-stage builds and inclusion of build tools in final images.","line":20},{"name":"Dependency Management Issues","description":"Problems with dependency installation such as lack of layer caching and inclusion of development dependencies.","line":25},{"name":"Build Context Problems","description":"Concerns about inefficient build context usage including copying unnecessary files and lack of .dockerignore optimization.","line":30},{"name":"Runtime Configuration Issues","description":"Runtime problems like running containers as root, missing health checks, and improper signal handling.","line":35},{"name":"Current Docker Compose Issues","description":"Issues in Docker Compose setup such as uniform large base images, redundant volume mounts, and missing resource limits.","line":40},{"name":"Multi-Stage Builds Optimization","description":"Optimization technique involving separating build and runtime stages to reduce image size and improve security.","line":48},{"name":"Layer Optimization","description":"Strategies to separate dependency installation from code copying and leverage caching for faster builds.","line":53},{"name":"Base Image Optimization","description":"Recommendations to use minimal base images like distroless or alpine to reduce image size and attack surface.","line":58},{"name":"Build Context Optimization","description":"Techniques to optimize the build context by using .dockerignore and conditional file inclusion.","line":63},{"name":"Service-Specific Optimizations","description":"Tailoring base images and dependencies per service to improve efficiency and reuse shared layers.","line":68},{"name":"Modern Python Packaging Best Practices","description":"Use of uv for dependency resolution, proper dependency groups, and wheel caching to improve build performance.","line":75},{"name":"Container Security Best Practices","description":"Security measures including running as non-root users, minimizing attack surface, and updating base images regularly.","line":80},{"name":"Build Performance Best Practices","description":"Recommendations for parallel builds, effective caching, and build context optimization to speed up build times.","line":85},{"name":"Runtime Efficiency Best Practices","description":"Ensuring proper signal handling, health checks, resource limits, and graceful shutdown for efficient container runtime.","line":90},{"name":"Target Image Sizes","description":"Defined goals for image sizes and build times to guide optimization efforts.","line":98},{"name":"Priority Optimizations List","description":"Ordered list of key optimizations to implement for improving Docker container builds and runtime.","line":103}]}
-->
<!-- FILE_MAP_END -->

# Knowledge Update: Docker Container Optimization (Generated 2025-01-15)

## Current State Analysis

### Docker Image Sizes (from previous builds):
- **docker_api**: 6.69GB
- **docker_worker-default**: 6.69GB
- **docker_worker-heavy**: 6.69GB
- **docker_worker-io**: 6.69GB
- **docker_flower**: 20.6GB (extremely bloated)

### Current Dockerfile Issues:

#### 1. Base Image Problems:
- Using `python:3.11-slim` (still large)
- No multi-stage builds
- Including build tools in final images

#### 2. Dependency Management Issues:
- Using `uv sync --frozen` without proper layer caching
- Installing all dependencies including dev dependencies
- No dependency layer separation

#### 3. Build Context Problems:
- Copying entire `src/` directory
- No .dockerignore optimization
- Including unnecessary files in build context

#### 4. Runtime Configuration Issues:
- No proper user creation (running as root)
- Missing health checks
- No proper signal handling

### Current Docker Compose Issues:
- All services using same large base image
- No service-specific optimizations
- Redundant volume mounts
- No resource limits

## Optimization Opportunities

### 1. Multi-Stage Builds:
- Separate build and runtime stages
- Use distroless or alpine for runtime
- Copy only necessary artifacts

### 2. Layer Optimization:
- Separate dependency installation from code copying
- Use dependency lock files for reproducible builds
- Cache dependency layers effectively

### 3. Base Image Optimization:
- Use distroless images for runtime
- Consider alpine variants
- Minimize system packages

### 4. Build Context Optimization:
- Implement proper .dockerignore
- Copy only necessary files
- Use build args for conditional inclusion

### 5. Service-Specific Optimizations:
- Different base images for different services
- Minimal dependencies per service
- Shared base layers where possible

## Best Practices for 2025

### 1. Modern Python Packaging:
- Use uv for faster dependency resolution
- Implement proper dependency groups
- Use wheel caching

### 2. Container Security:
- Non-root users
- Minimal attack surface
- Regular base image updates

### 3. Build Performance:
- Parallel builds where possible
- Effective layer caching
- Build context optimization

### 4. Runtime Efficiency:
- Proper signal handling
- Health checks
- Resource limits
- Graceful shutdown

## Implementation Guidance

### Target Image Sizes:
- **API/Workers**: < 500MB
- **Flower**: < 200MB
- **Build time**: < 5 minutes

### Priority Optimizations:
1. Implement multi-stage builds
2. Use distroless base images
3. Optimize dependency layers
4. Add proper .dockerignore
5. Implement service-specific optimizations