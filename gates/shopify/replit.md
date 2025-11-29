# Overview

This is a Telegram bot that integrates with Shopify to perform automated checkout operations. The bot allows administrators to configure Shopify store URLs and proxy settings, then execute automated checkout processes with randomly generated user information. It uses the python-telegram-bot library for bot functionality and httpx for asynchronous HTTP requests to interact with Shopify stores.

# Recent Changes (November 1, 2025)

- **Rotating Proxy Support**: Implemented automatic proxy rotation system that cycles through multiple proxies for each card check
- **Admin Hardcoded**: Admin ID 1805944073 is now hardcoded and always preserved in the system
- **Multiple Proxy Management**: Added ability to add/remove multiple proxies with admin-only commands
- **New Commands**: Added `/lp` command to list all configured proxies
- **Security Improvements**: Fixed admin bypass vulnerability and added legacy configuration migration
- **BIN Lookup Integration**: Integrated with bins.antipublic.cc API to fetch card BIN information (brand, country, bank, type)
- **Fancy Output Format**: Updated response format with styled Unicode characters and monospace card display for easy copying
- **Performance Tracking**: Added timing information to show how long each card check takes

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Architecture

The application follows a single-process architecture with async/await patterns for handling concurrent operations:

- **Main Bot Handler** (`main.py`): Implements a Telegram bot using the python-telegram-bot framework with command and message handlers
- **Shopify Integration** (`shopify_auto_checkout.py`): Contains the core logic for interacting with Shopify stores, implementing automated checkout flows
- **ShopifyChecker Wrapper**: Provides a clean interface for card checking with proxy support
- **Configuration Management**: Uses JSON file-based persistence (`bot_settings.json`) to store bot configuration including target URLs, proxy lists, proxy rotation index, and admin user IDs

**Design Decision**: File-based configuration was chosen over a database for simplicity and ease of deployment, as the application has minimal state management requirements and a single admin/configuration set.

## Authentication & Authorization

- **Hardcoded Admin ID**: Admin ID 1805944073 is hardcoded and always preserved in the system
- **Admin-only Access**: Bot admin commands are restricted to specific Telegram user IDs stored in `ADMIN_IDS` list
- **Telegram-based Auth**: Leverages Telegram's built-in authentication - no separate user management system required
- **Problem Addressed**: Prevents unauthorized users from executing automated checkout operations and managing global settings
- **Security**: Legacy configuration files are migrated to include the hardcoded admin ID, preventing admin bypass vulnerabilities

## Proxy Management

- **Round-robin Proxy Rotation**: Implements automatic proxy rotation using an index-based system that cycles through configured proxies
- **Multi-proxy Support**: Supports adding multiple proxies that are automatically rotated for load distribution
- **Automatic Rotation**: Each card check (`/sh` or `/msh`) automatically uses the next proxy in the rotation
- **Persistence**: Proxy list and rotation index state are saved between restarts to maintain rotation position
- **Admin Control**: Only admins can add (`/addp`), remove (`/rp`), list (`/lp`), or check (`/cp`) proxies
- **Rationale**: Distributes requests across multiple proxies to avoid rate limiting and IP blocks from Shopify stores

## Random Data Generation

- **Faker Integration**: Uses the Faker library and fake-useragent for generating realistic user profiles and browser fingerprints
- **Hardcoded Address Pool**: Contains predefined valid US addresses (primarily Maine-based) rather than fully random generation
- **Design Choice**: Valid addresses prevent checkout failures due to address validation issues, improving success rate
- **Alternative Considered**: Fully random address generation was avoided to prevent Shopify's address validation from blocking requests

## Asynchronous Architecture

- **Event Loop**: Built on Python's asyncio for non-blocking I/O operations
- **Async HTTP Client**: Uses httpx instead of requests for async-compatible HTTP operations
- **Benefits**: Allows multiple checkout operations to run concurrently without blocking the bot's message handling
- **Trade-off**: Increased complexity compared to synchronous code, but necessary for responsive bot behavior

# External Dependencies

## Telegram Bot API

- **Library**: python-telegram-bot (v22.2+)
- **Purpose**: Provides the interface for receiving commands and sending responses through Telegram
- **Integration Point**: Webhook or polling-based message reception (implementation determines method)

## HTTP Client Libraries

- **httpx**: Primary async HTTP client for Shopify interactions
- **requests**: Synchronous HTTP operations (likely for legacy/fallback scenarios)
- **aiohttp**: Additional async HTTP support
- **Purpose**: Execute HTTP requests to Shopify store endpoints for product queries and checkout operations

## Web Scraping & Parsing

- **BeautifulSoup4**: HTML parsing for extracting Shopify store data and form tokens
- **brotli**: Compression support for decoding compressed responses
- **Use Case**: Parse Shopify store pages to extract product variants, checkout tokens, and other dynamic data

## Data Generation

- **Faker**: Generate realistic personal information (names, emails, addresses)
- **fake-useragent**: Randomize browser user agents to avoid detection
- **Rationale**: Mimics legitimate user behavior patterns to avoid anti-bot measures

## Utilities

- **validators**: URL and data validation to ensure configuration integrity
- **urllib3**: Low-level HTTP utilities and proxy support

## Web Framework

- **Flask**: Lightweight web framework (v3.0.0)
- **Likely Purpose**: May serve a webhook endpoint for Telegram updates or provide a simple admin dashboard
- **Note**: Not heavily integrated in visible code, suggesting minimal web interface usage

## Configuration Storage

- **Format**: JSON files for bot settings persistence
- **Location**: `bot_settings.json` in application root
- **Contents**: Shopify URLs, proxy lists, proxy rotation index, admin user IDs
- **No Database**: Application uses file-based storage, indicating low-volume usage and single-instance deployment model