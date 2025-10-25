# API Documentation

## Overview
This document describes the REST API endpoints for TheTakeoutBoxCalHacks application.

## Endpoints

### Crime Data
- `GET /api/crimes` - Retrieve crime data
- `GET /api/crimes/{id}` - Get specific crime details

### Routing
- `POST /api/routes` - Calculate safe routes between points
- `GET /api/routes/{id}` - Get route details

### Locations
- `POST /api/locations` - Save user locations
- `GET /api/locations` - Retrieve saved locations
- `DELETE /api/locations/{id}` - Remove saved location

### Letta Integration
- `POST /api/memory` - Store memory with Letta
- `GET /api/memory` - Retrieve memories
