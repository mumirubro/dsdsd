# Overview

TOJI CHK Bot is a Telegram bot designed to validate Stripe payment cards through WooCommerce-based websites. The bot supports three distinct authentication strategies to handle different site configurations: creating new temporary accounts, using shared credentials, or bypassing authentication entirely by directly accessing Stripe's public API keys.

## Recent Updates (November 11, 2025)

- **Critical Security Fix**: Removed hardcoded Stripe publishable key fallback that could leak card data to unrelated accounts
- **Mode 3 Enhanced**: Now falls back to Mode 1 automatically when Stripe key cannot be found on public pages
- **Security Hardening**: Card data is never sent to third-party Stripe accounts - all modes require site-derived keys or fail safely
- **Configuration Persistence**: Settings loaded automatically on bot startup from bot_config.json
- **Error Handling**: Comprehensive error messages for all failure scenarios

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Platform**: Telegram Bot API using `python-telegram-bot` library
- **Architecture Pattern**: Command-based conversational interface with state management
- **Rationale**: Telegram provides a user-friendly interface for card checking operations while maintaining security through bot tokens and admin controls

## Authentication Modes

The system implements three distinct authentication strategies to adapt to different WooCommerce/Stripe configurations:

### Mode 1: Temporary Account Creation (Default)
- Creates a new WooCommerce account for each card check
- Generates random email addresses and credentials
- **Use case**: Sites that allow unrestricted new registrations
- **Pros**: No credential management, clean session per check
- **Cons**: May fail on sites with registration restrictions

### Mode 2: Shared Account Login
- Uses admin-configured credentials stored globally
- All users authenticate with the same WooCommerce account
- **Use case**: Sites that block frequent new registrations
- **Pros**: Bypasses registration limits, consistent session
- **Cons**: Requires admin to maintain working credentials

### Mode 3: Direct Stripe API Access
- Bypasses WooCommerce authentication entirely
- Scrapes Stripe public keys from public pages (checkout, cart, homepage)
- Directly validates cards against Stripe API
- **Fallback**: Reverts to Mode 1 if Stripe key not found on public pages
- **Use case**: Sites exposing Stripe keys without authentication
- **Pros**: Fastest method, no account management
- **Cons**: Only works if Stripe key is publicly accessible

## Configuration Management

### Persistent Storage
- **Format**: JSON-based configuration file (`bot_config.json`)
- **Concurrency**: Async file locks to prevent race conditions
- **Data Structure**:
  - `stripe_url`: Target WooCommerce domain
  - `auth_mode`: Selected authentication strategy (1-3)
  - `shared_email`: Credentials for Mode 2
  - `shared_password`: Credentials for Mode 2

### State Management
- **Pattern**: Conversation handler with defined states
- **States**: `AWAITING_AUTH_MODE`, `AWAITING_CREDENTIALS`
- **Rationale**: Multi-step configuration flow requires tracking user's position in setup process

## Card Validation Flow

### Input Parsing
- **Format**: `card_number|mm|yy|cvv`
- **Validation**: Ensures all four components are present before processing
- **Batch Support**: Multiple cards (max 10) via `/mchk` command

### HTTP Request Pattern
- **Library**: `aiohttp` for async HTTP operations
- **Session Management**: Maintains cookies and session state across requests
- **User-Agent Rotation**: Uses `fake-useragent` to avoid detection
- **Flow**:
  1. Access WooCommerce my-account page
  2. Extract nonces and CSRF tokens via string parsing
  3. Authenticate (or skip based on mode)
  4. Submit card to Stripe payment method endpoint
  5. Parse response for validation status

### Response Parsing
- **Method**: String extraction using custom `gets()` function
- **Targets**: 
  - WooCommerce nonces (`woocommerce-add-payment-method-nonce`)
  - Stripe tokens and client secrets
  - Error messages and success indicators
- **Rationale**: Lightweight parsing without heavy dependencies like BeautifulSoup for simple extraction tasks

## Access Control

### Role-Based Authorization
- **Admin IDs**: Hardcoded list of authorized Telegram user IDs
- **Admin Commands**: `/setsurl`, `/mysurl`, `/rmsurl`, `/chkurl`, `/mschku`
- **User Commands**: `/chk`, `/mchk`
- **Rationale**: Prevents unauthorized users from modifying global configuration while allowing card checks

## URL Normalization

- **Default Protocol**: HTTPS
- **Path Standardization**: Appends `/my-account` if not present
- **Trailing Slash Handling**: Ensures consistent URL format
- **Purpose**: Handles various user input formats and ensures consistent API endpoints

# External Dependencies

## Telegram API
- **Library**: `python-telegram-bot`
- **Purpose**: Bot interface, command handling, message delivery
- **Authentication**: Bot token via environment variable `BOT_TOKEN`

## Stripe API
- **Usage**: Direct card validation in Mode 3
- **Access**: Public keys scraped from target websites
- **Endpoints**: Payment method creation and validation

## WooCommerce Integration
- **Protocol**: HTTP/HTTPS requests to WooCommerce endpoints
- **Endpoints**:
  - `/my-account/` - Account access
  - `/my-account/add-payment-method/` - Payment method management
  - Registration/login forms
- **Authentication**: Session-based via cookies and nonces

## Third-Party Services
- **BIN Lookup**: `bins.antipublic.cc` for card metadata (brand, bank, country)
- **Purpose**: Enriches card validation responses with issuer information

## HTTP Client
- **Library**: `aiohttp`
- **Rationale**: Async/await support for concurrent operations, better performance for multiple card checks

## Utility Libraries
- **fake-useragent**: Generates realistic browser user-agent strings
- **Purpose**: Avoid bot detection by rotating user agents