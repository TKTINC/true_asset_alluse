# True-Asset-ALLUSE API Reference

**Version**: 1.0
**Date**: 2024-07-26
**Author**: Manus AI

## 1. Introduction

This document provides a comprehensive reference for the True-Asset-ALLUSE API. The API provides programmatic access to all system functionalities, allowing you to integrate the platform with your own applications and workflows.

## 2. Authentication

All API requests must be authenticated using a JSON Web Token (JWT). You can obtain a JWT by providing your API key and secret to the authentication endpoint.

**Endpoint**: `/api/v1/auth/token`
**Method**: `POST`

## 3. API Endpoints

This section provides a detailed description of all API endpoints.

### 3.1. Accounts

- `GET /api/v1/accounts`: Get all accounts
- `GET /api/v1/accounts/{account_id}`: Get a specific account
- `POST /api/v1/accounts`: Create a new account
- `PUT /api/v1/accounts/{account_id}`: Update an account
- `DELETE /api/v1/accounts/{account_id}`: Delete an account

### 3.2. Positions

- `GET /api/v1/positions`: Get all positions
- `GET /api/v1/positions/{position_id}`: Get a specific position

### 3.3. Orders

- `GET /api/v1/orders`: Get all orders
- `GET /api/v1/orders/{order_id}`: Get a specific order
- `POST /api/v1/orders`: Create a new order
- `DELETE /api/v1/orders/{order_id}`: Cancel an order

### 3.4. Market Data

- `GET /api/v1/market/quotes`: Get real-time quotes
- `GET /api/v1/market/trades`: Get real-time trades
- `GET /api/v1/market/options`: Get option chains

### 3.5. Portfolio Management

- `POST /api/v1/portfolio/optimize`: Optimize a portfolio
- `GET /api/v1/portfolio/performance`: Get portfolio performance
- `GET /api/v1/portfolio/risk`: Get portfolio risk analysis

### 3.6. Reporting

- `POST /api/v1/reports`: Generate a new report
- `GET /api/v1/reports/{report_id}`: Get a specific report

## 4. Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request. The response body will contain a detailed error message in case of failure.

## 5. Rate Limiting

The API is rate-limited to prevent abuse. You can check the rate limit status in the response headers of each request.

## 6. Conclusion

The True-Asset-ALLUSE API provides a powerful and flexible way to integrate the platform with your own applications. If you have any questions or need assistance, please contact our support team.


### 3.6. Natural Language Interface (WS7)

#### 3.6.1. Chatbot Endpoints

- `POST /api/v1/chat/query`: Process natural language query
  - **Description**: Submit a natural language query to the wealth chatbot
  - **Request Body**: 
    ```json
    {
      "query": "What's our current portfolio performance?",
      "user_context": {
        "user_id": "user123",
        "session_id": "session456"
      }
    }
    ```
  - **Response**: 
    ```json
    {
      "response": "Your current portfolio performance shows...",
      "confidence": 0.95,
      "sources": ["portfolio_manager", "performance_analyzer"],
      "conversation_id": "conv789"
    }
    ```

- `GET /api/v1/chat/history/{conversation_id}`: Get conversation history
  - **Description**: Retrieve conversation history for a specific session
  - **Response**: Array of conversation messages with timestamps

- `POST /api/v1/chat/feedback`: Submit feedback on chatbot response
  - **Description**: Provide feedback to improve chatbot responses
  - **Request Body**:
    ```json
    {
      "conversation_id": "conv789",
      "message_id": "msg123",
      "rating": 5,
      "feedback": "Very helpful response"
    }
    ```

#### 3.6.2. Narrative Generation Endpoints

- `POST /api/v1/narrative/generate`: Generate report narrative
  - **Description**: Generate natural language narrative for reports
  - **Request Body**:
    ```json
    {
      "report_type": "performance",
      "data": {...},
      "style": "professional",
      "language": "en"
    }
    ```
  - **Response**:
    ```json
    {
      "narrative": "This week's performance showed...",
      "generation_time": 2.3,
      "quality_score": 0.92
    }
    ```

- `GET /api/v1/narrative/templates`: Get available narrative templates
  - **Description**: Retrieve list of available narrative templates
  - **Response**: Array of template definitions with descriptions

### 3.7. Machine Learning & Intelligence (WS8)

#### 3.7.1. Intelligence Coordinator Endpoints

- `GET /api/v1/intelligence/current`: Get current system intelligence
  - **Description**: Retrieve the latest system intelligence snapshot
  - **Response**:
    ```json
    {
      "timestamp": "2024-07-26T10:30:00Z",
      "market_conditions": {...},
      "system_performance": {...},
      "risk_metrics": {...},
      "active_patterns": [...],
      "anomaly_count": 2,
      "forecast_confidence": 0.78
    }
    ```

- `POST /api/v1/intelligence/report`: Generate intelligence report
  - **Description**: Generate comprehensive intelligence report
  - **Request Body**:
    ```json
    {
      "report_type": "comprehensive",
      "time_range": "7d",
      "include_forecasts": true
    }
    ```

- `GET /api/v1/intelligence/status`: Get system status
  - **Description**: Get status of all ML intelligence components

#### 3.7.2. Anomaly Detection Endpoints

- `GET /api/v1/anomalies/recent`: Get recent anomaly alerts
  - **Description**: Retrieve recent anomaly alerts with filtering options
  - **Query Parameters**:
    - `hours_back`: Number of hours to look back (default: 24)
    - `severity`: Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
    - `anomaly_type`: Filter by anomaly type
  - **Response**:
    ```json
    {
      "alerts": [
        {
          "alert_id": "alert123",
          "anomaly_type": "MARKET_VOLATILITY",
          "severity": "HIGH",
          "confidence": 0.87,
          "description": "Unusual volatility spike detected",
          "detected_at": "2024-07-26T09:15:00Z",
          "affected_metrics": {...},
          "recommendations": [...]
        }
      ],
      "total_count": 5
    }
    ```

- `GET /api/v1/anomalies/statistics`: Get anomaly detection statistics
  - **Description**: Get comprehensive statistics about anomaly detection
  - **Response**: Statistics including detection rates, types, and performance metrics

#### 3.7.3. Pattern Recognition Endpoints

- `GET /api/v1/patterns/recent`: Get recent pattern matches
  - **Description**: Retrieve recently detected market patterns
  - **Query Parameters**:
    - `days_back`: Number of days to look back (default: 7)
    - `pattern_type`: Filter by pattern type
    - `min_confidence`: Minimum confidence threshold
  - **Response**:
    ```json
    {
      "patterns": [
        {
          "pattern_id": "pattern123",
          "pattern_type": "MARKET_REGIME",
          "name": "High Volatility Regime",
          "match_confidence": 0.85,
          "match_strength": 0.92,
          "expected_outcomes": {...},
          "recommendations": [...],
          "matched_at": "2024-07-26T08:00:00Z"
        }
      ]
    }
    ```

- `GET /api/v1/patterns/library`: Get pattern library
  - **Description**: Retrieve all known patterns in the system
  - **Response**: Array of pattern definitions with historical performance

#### 3.7.4. Predictive Analytics Endpoints

- `GET /api/v1/forecasts/active`: Get active forecasts
  - **Description**: Retrieve all active predictive forecasts
  - **Response**:
    ```json
    {
      "forecasts": [
        {
          "forecast_id": "forecast123",
          "forecast_name": "Weekly Performance Forecast",
          "forecast_horizon": "7d",
          "overall_confidence": 0.75,
          "predictions": [...],
          "key_assumptions": [...],
          "risk_factors": [...],
          "created_at": "2024-07-26T00:00:00Z"
        }
      ]
    }
    ```

- `POST /api/v1/forecasts/generate`: Generate new forecast
  - **Description**: Generate a new predictive forecast
  - **Request Body**:
    ```json
    {
      "forecast_type": "performance",
      "horizon_days": 7,
      "confidence_threshold": 0.7,
      "include_scenarios": true
    }
    ```

#### 3.7.5. Adaptive Learning Endpoints

- `GET /api/v1/learning/insights`: Get learning insights
  - **Description**: Retrieve insights from the adaptive learning engine
  - **Query Parameters**:
    - `insight_type`: Filter by insight type
    - `min_confidence`: Minimum confidence threshold
    - `days_back`: Time range for insights

- `GET /api/v1/learning/performance`: Get model performance metrics
  - **Description**: Get performance metrics for all learning models
  - **Response**: Model accuracy, training status, and performance statistics

- `POST /api/v1/learning/retrain`: Trigger model retraining
  - **Description**: Manually trigger retraining of learning models
  - **Request Body**:
    ```json
    {
      "model_type": "week_type_prediction",
      "force_retrain": false
    }
    ```

## 4. Enhanced Error Handling

With WS7 and WS8 integration, additional error codes are available:

- `4001`: Natural language query parsing failed
- `4002`: Chatbot service unavailable
- `4003`: Narrative generation failed
- `4004`: ML model not trained
- `4005`: Insufficient data for analysis
- `4006`: Anomaly detection service unavailable
- `4007`: Pattern recognition failed
- `4008`: Forecast generation failed

## 5. Rate Limiting

Enhanced rate limiting for AI-powered endpoints:

- **Chatbot queries**: 100 requests per minute per user
- **Narrative generation**: 20 requests per minute per user
- **Intelligence reports**: 10 requests per minute per user
- **ML analytics**: 50 requests per minute per user

## 6. Webhooks

New webhook events for WS7 and WS8:

- `anomaly.detected`: Triggered when a new anomaly is detected
- `pattern.matched`: Triggered when a new pattern is matched
- `forecast.generated`: Triggered when a new forecast is created
- `intelligence.updated`: Triggered when system intelligence is updated
- `chat.conversation.started`: Triggered when a new chat conversation begins

