# Proxy Configuration Guide

## Overview
The Crunchyroll Checker Bot now supports proxy configuration for all account checking requests. This helps prevent rate limiting and blocks by routing requests through proxy servers.

## Admin Access
Only the admin (User ID: 1805944073) can manage proxies.

## Commands

### `/pc` - Add Proxy Configuration
Add a single proxy to the bot. The bot supports multiple proxy formats:

#### Supported Formats:

1. **Simple Proxy** (IP:PORT)
   ```
   /pc 192.168.1.1:8080
   ```

2. **Authenticated Proxy** (IP:PORT:USERNAME:PASSWORD)
   ```
   /pc 192.168.1.1:8080:myuser:mypass
   ```

3. **HTTP Proxy with URL**
   ```
   /pc http://proxy.example.com:3128
   ```

4. **HTTP Proxy with Authentication**
   ```
   /pc http://username:password@proxy.example.com:3128
   ```

**Note:** SOCKS5 proxies are not currently supported (requires additional aiohttp-socks package).

### `/listproxy` - List All Proxies
View all configured proxies with their indices.

```
/listproxy
```

### `/delproxy <index>` - Delete a Proxy
Remove a specific proxy by its index number.

```
/delproxy 0
```

### `/clearproxy` - Clear All Proxies
Remove all configured proxies. The bot will then make direct connections.

```
/clearproxy
```

## How It Works

1. **Proxy Rotation**: When multiple proxies are configured, the bot automatically rotates between them for each request.

2. **Automatic Usage**: Once proxies are configured, they are automatically used for all Crunchyroll account checks.

3. **Persistent Storage**: Proxies are saved to `proxies.json` and persist across bot restarts.

## Best Practices for Replit

### To Avoid Replit Bans:

1. **Use Residential Proxies**: Prefer residential proxies over datacenter proxies for better success rates.

2. **Rotate Proxies**: Add multiple proxies to distribute the load:
   ```
   /pc 1.2.3.4:8080
   /pc 5.6.7.8:8080
   /pc 9.10.11.12:8080
   ```

3. **Use Authenticated Proxies**: These are more secure and reliable:
   ```
   /pc proxy1.com:8080:user:pass
   /pc proxy2.com:8080:user:pass
   ```

4. **Monitor Performance**: If you get blocked, add more proxies or switch to different proxy providers.

5. **Rate Limiting**: The bot already has a 2-second delay between mass checks, which helps prevent rate limiting.

## Proxy Providers

Popular proxy providers that work well:

- **Bright Data** (formerly Luminati)
- **Smartproxy**
- **Oxylabs**
- **IPRoyal**
- **Webshare**

## Troubleshooting

### Proxies Not Working?

1. **Check Format**: Ensure the proxy format is correct.
2. **Test Proxy**: Verify the proxy is working outside the bot.
3. **Remove Invalid Proxies**: Use `/delproxy <index>` to remove non-working proxies.
4. **Clear and Restart**: Use `/clearproxy` and add proxies again.

### Still Getting Blocked?

1. **Add More Proxies**: Increase your proxy pool.
2. **Use Better Proxies**: Switch to residential or premium proxies.
3. **Check Proxy Provider**: Some providers may have blocked IPs.

## Security Notes

- Proxies are stored locally in `proxies.json`
- Only the admin can view and manage proxies
- Proxy credentials are stored in plain text (keep your Replit private)
- Consider using environment variables for sensitive proxy credentials in production

## Example Workflow

1. **Add multiple proxies**:
   ```
   /pc http://user1:pass1@proxy1.com:8080
   /pc http://user2:pass2@proxy2.com:8080
   /pc http://user3:pass3@proxy3.com:8080
   ```

2. **Verify they're added**:
   ```
   /listproxy
   ```

3. **Test account checking**:
   ```
   /cr test@example.com:password123
   ```

4. **Monitor and manage**:
   - If a proxy fails, use `/delproxy <index>` to remove it
   - Add new proxies as needed with `/pc`

## Safety Tips

✅ **DO:**
- Use reputable proxy providers
- Rotate proxies regularly
- Monitor your usage
- Keep proxy credentials secure

❌ **DON'T:**
- Share your proxy credentials
- Use free public proxies (unreliable and often blocked)
- Overload a single proxy with too many requests
- Forget to update expired proxies

---

**Need Help?**
Contact the bot admin if you have questions about proxy configuration.
