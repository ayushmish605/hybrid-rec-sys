# Utilities Module

## Purpose
Common utility functions used across the project.

## Components

### 1. `logger.py` - Logging Configuration
- **Purpose**: Centralized logging setup for all modules
- **Input**: Module name (str)
- **Output**: Configured logger instance
- **Features**:
  - Logs to both console and file (`logs/app.log`)
  - Rotating file handler (max 10MB, keeps 3 backups)
  - Timestamped entries with level indicators
  - Color-coded console output (if terminal supports it)
  - Different log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Usage

```python
from utils.logger import setup_logger

# Create logger for your module
logger = setup_logger(__name__)

# Use logger
logger.info("Starting process...")
logger.warning("This might be a problem")
logger.error("Something went wrong!")
logger.debug("Detailed debugging info")
```

## Log Format
```
2024-12-07 14:30:45 - module_name - INFO - Message here
```

## Log Locations
- **Console**: Real-time output with colors
- **File**: `logs/app.log` (persistent, rotated)
- **Rotation**: When file reaches 10MB, creates `app.log.1`, `app.log.2`, etc.

## Log Levels by Module
- **Scrapers**: INFO level (shows scraping progress, errors)
- **Database**: DEBUG level (shows SQL operations)
- **Gemini**: INFO level (shows API calls, responses)
- **Preprocessing**: INFO level (shows analysis progress)

## Best Practices
1. Always create module-level logger: `logger = setup_logger(__name__)`
2. Use appropriate levels:
   - DEBUG: Detailed diagnostic info
   - INFO: General progress/status
   - WARNING: Recoverable issues
   - ERROR: Serious problems
   - CRITICAL: System-breaking failures
3. Include context in messages: `logger.info(f"Scraped {count} reviews for {movie_title}")`
4. Log exceptions with traceback: `logger.error(f"Failed: {e}", exc_info=True)`
