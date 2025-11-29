# Overview

This is a Netflix automation tool built with Python and Playwright. The application automates browser interactions with Netflix's website, handling tasks such as authentication flows, cookie management, and web scraping. It uses headless browser automation to interact with Netflix programmatically while mimicking real user behavior to avoid detection.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Browser Automation Framework

**Technology**: Playwright (async Python API)

The system uses Playwright's async API for browser automation rather than Selenium or Puppeteer. This decision provides:
- Better performance through native async/await support
- More reliable element detection and interaction
- Built-in support for multiple browser engines (Chromium is used here)

## Anti-Detection Strategy

**Approach**: Browser fingerprint masking and human-like behavior simulation

The application implements several anti-bot detection measures:
- Custom browser launch arguments to disable automation flags (`--disable-blink-features=AutomationControlled`)
- Realistic viewport dimensions (1920x1080)
- Authentic user agent strings matching real Chrome browsers
- Locale and timezone spoofing (US-based)
- Custom HTTP headers to mimic legitimate browser requests

**Rationale**: Netflix and similar services employ sophisticated bot detection. These measures help the automation appear as a legitimate user session.

## State Management

**Architecture**: In-memory state storage with cookie persistence

The `NetflixAutomation` class maintains:
- Browser instance lifecycle management
- Cookies dictionary for session persistence
- Flow data dictionary for multi-step process tracking
- Country/phone code configuration for regional settings

**Design Pattern**: Single class encapsulation with async context management

This keeps related automation logic together and ensures proper resource cleanup through async lifecycle methods.

## Configuration System

**Approach**: Constructor-based configuration

Key configuration options:
- `debug`: Enables verbose logging for troubleshooting
- `headless`: Controls visible vs. headless browser mode
- Regional settings (country_code, phone_code) for localization

This allows flexible deployment modes - visible for development/debugging, headless for production automation.

## Error Handling & Debugging

**Strategy**: Conditional debug logging

The `log_debug` method provides development visibility without production overhead. This lightweight approach is suitable for automation scripts where full logging frameworks might be excessive.

# External Dependencies

## Browser Automation

- **Playwright**: Core browser automation library
  - Async API for Python
  - Chromium browser engine
  - Handles browser launching, context creation, and page interactions

## Runtime Environment

- **Python asyncio**: Native async/await support for concurrent operations
- **Type hints**: Uses `typing` module for static type checking and code clarity

## Data Handling

- **json**: For parsing and serializing cookies/configuration data
- **re**: Regular expressions for pattern matching and data extraction

## Network Layer

The application intercepts and manages:
- HTTP cookies for session persistence
- Custom headers for authentication flows
- Response data extraction from Netflix's APIs

## Platform Requirements

Based on browser launch arguments:
- Requires sufficient memory (--disable-dev-shm-usage suggests container/limited memory environments)
- GPU is disabled, indicating server/headless deployment target
- Sandbox disabled for containerized environments (Docker, etc.)