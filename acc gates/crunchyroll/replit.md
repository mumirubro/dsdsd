# Crunchyroll Checker Telegram Bot

## Overview

A Telegram bot that validates Crunchyroll account credentials through automated HTTP requests. The bot supports single account checking (`/cr`) and mass checking (`/mcr`), with features including Cloudflare challenge bypass, proxy rotation, and admin-controlled proxy management. The bot uses asyncio for concurrent operations and provides real-time feedback through Telegram message updates.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

**Monolithic Architecture**: Single-file application (`cr.py`) combining HTTP automation, Cloudflare bypass logic, and Telegram bot handlers. This design prioritizes simplicity and ease of deployment on Replit.

**Rationale**: For a bot with limited scope and features, a monolithic structure reduces complexity and eliminates inter-service communication overhead. The entire application state is managed in-memory with file-based persistence for proxies.

### Core Components

**1. HTTP Request Engine**

Uses `aiohttp` for async HTTP operations with custom session management:
- Cloudflare challenge detection via JavaScript URL pattern matching
- User-Agent rotation using `fake_useragent` library
- Custom cookie handling and header management
- Proxy rotation with automatic fallback

**Alternatives Considered**: `httpx` was considered for HTTP/2 support, but `aiohttp` provides better async integration and is more battle-tested for web scraping.

**2. Telegram Bot Interface**

Built on `python-telegram-bot` library (async version):
- Command handlers for `/cr`, `/mcr`, `/pc`, `/listproxy`, `/delproxy`
- Message handlers for combo file processing
- Real-time progress updates via message editing
- Admin-only commands with user ID validation

**Rationale**: The official `python-telegram-bot` library provides robust async support and comprehensive API coverage, essential for handling concurrent checks and live message updates.

**3. Proxy Management System**

Custom `ProxyManager` class with features:
- Multi-format proxy support (IP:PORT, authenticated, HTTP URLs)
- Round-robin rotation strategy
- JSON file-based persistence (`proxies.json`)
- Runtime proxy addition/removal via Telegram commands

**Design Decision**: File-based storage over database for simplicity. The proxy list is typically small (<100 entries) and doesn't require complex querying.

**Pros**: 
- Zero database dependencies
- Instant read/write operations
- Easy manual editing and backup

**Cons**:
- No concurrent write protection (acceptable for single-admin use case)
- Limited scalability (not an issue for current scope)

### Authentication & Authorization

**Admin-Only Commands**: Simple user ID comparison (`ADMIN_ID` environment variable). Commands `/pc`, `/delproxy` check `update.effective_user.id` before execution.

**Rationale**: Bot has single-admin architecture. More complex role systems (e.g., group permissions) would add unnecessary overhead.

### Error Handling Strategy

**Progressive Degradation**:
- Cloudflare challenges trigger JavaScript parsing attempts
- Failed proxy requests rotate to next available proxy
- Telegram API errors (e.g., message edit failures) are logged but don't crash the bot
- Invalid account formats return user-friendly error messages

**Known Issue**: Markdown parsing errors in message updates (see error log) indicate incomplete entity escaping. This should be addressed by sanitizing response text before sending.

### Data Flow

1. **Single Check (`/cr`)**:
   - Parse email:password combo
   - Select proxy from rotation pool
   - Send login request with fake User-Agent
   - Detect Cloudflare challenges
   - Parse response for account status
   - Format and send result via Telegram

2. **Mass Check (`/mcr`)**:
   - Receive combo file as message
   - Parse line-by-line
   - Execute checks concurrently with semaphore limit
   - Aggregate results
   - Send formatted summary

3. **Proxy Management**:
   - Admin sends `/pc <proxy>`
   - Validate proxy format
   - Append to in-memory list
   - Persist to `proxies.json`
   - Confirm via Telegram message

### Concurrency Model

**AsyncIO Event Loop**: All I/O operations (HTTP requests, Telegram API calls) use async/await pattern.

**Semaphore Control**: Mass checks use semaphore to limit concurrent HTTP requests, preventing resource exhaustion and reducing ban risk.

**Rationale**: Python's asyncio is ideal for I/O-bound operations like HTTP requests. Threading would add complexity without performance benefits.

## External Dependencies

### Third-Party Libraries

- **python-telegram-bot**: Telegram Bot API wrapper (async version)
- **aiohttp**: Async HTTP client for account checking requests
- **beautifulsoup4**: HTML parsing for Cloudflare challenge responses
- **fake-useragent**: Random User-Agent generation for bot detection evasion
- **lxml**: HTML parser backend for BeautifulSoup (faster than built-in)

### External Services

**Telegram Bot API**: 
- Endpoint: `https://api.telegram.org/bot<TOKEN>/`
- Used for: Receiving commands, sending messages, editing messages
- Authentication: Bot token stored in `TELEGRAM_BOT_TOKEN` environment variable

**Crunchyroll Web Services**:
- Login endpoint: `https://www.crunchyroll.com/` (exact endpoint determined by form parsing)
- Cloudflare CDN: `https://www.crunchyroll.com/cdn-cgi/challenge-platform/`
- Response handling: HTML parsing for success/error indicators

**Proxy Servers** (User-Configured):
- HTTP proxies with optional authentication
- Rotated per request to distribute load
- No specific provider dependency

### Configuration

**Environment Variables**:
- `TELEGRAM_BOT_TOKEN`: Bot authentication token (required)
- `BOT_CREATOR`: Credit string for bot creator
- `ADMIN_ID`: Numeric user ID with admin privileges

**File-Based Storage**:
- `proxies.json`: Proxy list persistence (JSON array format)

### Deployment Environment

Designed for **Replit** deployment:
- Single-file structure for easy execution
- Environment variable configuration via Replit Secrets
- No database requirements (file-based storage only)
- Minimal resource footprint (async I/O reduces thread overhead)