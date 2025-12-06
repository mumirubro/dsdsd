"""
Advanced Proxy Checker Tool
Supports all proxy types: HTTP, HTTPS, SOCKS4, SOCKS5, Rotating proxies
Provides detailed information about proxy status, IP, location, speed, anonymity
"""

import asyncio
import aiohttp
import time
import re
import socket
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse


class ProxyChecker:
    """Advanced proxy checker with multi-protocol support"""
    
    def __init__(self):
        self.test_urls = [
            'https://api.ipify.org?format=json',
            'https://httpbin.org/ip',
            'https://icanhazip.com',
        ]
        self.geo_url = 'http://ip-api.com/json/'
        self.timeout = 15
        
    def parse_proxy(self, proxy_string: str) -> Dict[str, Any]:
        """Parse proxy string into components - supports all formats"""
        proxy_string = proxy_string.strip()
        
        result = {
            'type': 'http',
            'host': None,
            'port': None,
            'username': None,
            'password': None,
            'original': proxy_string,
            'formatted': None
        }
        
        if proxy_string.startswith('socks5://'):
            result['type'] = 'socks5'
            proxy_string = proxy_string[9:]
        elif proxy_string.startswith('socks4://'):
            result['type'] = 'socks4'
            proxy_string = proxy_string[9:]
        elif proxy_string.startswith('https://'):
            result['type'] = 'https'
            proxy_string = proxy_string[8:]
        elif proxy_string.startswith('http://'):
            result['type'] = 'http'
            proxy_string = proxy_string[7:]
        
        if '@' in proxy_string:
            auth_part, host_part = proxy_string.rsplit('@', 1)
            if ':' in auth_part:
                result['username'], result['password'] = auth_part.split(':', 1)
            host_port = host_part
        else:
            host_port = proxy_string
        
        parts = host_port.split(':')
        if len(parts) >= 2:
            if len(parts) == 4 and result['username'] is None:
                # Standard format: host:port:user:pass
                result['host'] = parts[0]
                result['port'] = int(parts[1])
                result['username'] = parts[2]
                result['password'] = parts[3]
            elif len(parts) > 4 and result['username'] is None:
                # BrightData format where username contains colons: host:port:user-with-colons:pass
                result['host'] = parts[0]
                result['port'] = int(parts[1])
                result['password'] = parts[-1]  # Last part is password
                result['username'] = ':'.join(parts[2:-1])  # Everything between port and password is username
            elif len(parts) == 2:
                result['host'] = parts[0]
                result['port'] = int(parts[1])
            else:
                result['host'] = parts[0]
                try:
                    result['port'] = int(parts[1])
                except:
                    result['port'] = 8080
        else:
            result['host'] = host_port
            result['port'] = 8080
        
        if result['username'] and result['password']:
            result['formatted'] = f"{result['type']}://{result['username']}:{result['password']}@{result['host']}:{result['port']}"
        else:
            result['formatted'] = f"{result['type']}://{result['host']}:{result['port']}"
        
        return result
    
    async def get_own_ip(self) -> Optional[str]:
        """Get our own IP for comparison"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get('https://api.ipify.org?format=json') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('ip')
        except:
            pass
        return None
    
    async def get_geo_info(self, ip: str) -> Dict[str, Any]:
        """Get geographic information for an IP"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f'{self.geo_url}{ip}') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            'country': data.get('country', 'Unknown'),
                            'country_code': data.get('countryCode', 'XX'),
                            'region': data.get('regionName', 'Unknown'),
                            'city': data.get('city', 'Unknown'),
                            'isp': data.get('isp', 'Unknown'),
                            'org': data.get('org', 'Unknown'),
                            'as': data.get('as', 'Unknown'),
                            'timezone': data.get('timezone', 'Unknown'),
                            'lat': data.get('lat', 0),
                            'lon': data.get('lon', 0),
                        }
        except:
            pass
        return {
            'country': 'Unknown',
            'country_code': 'XX',
            'region': 'Unknown',
            'city': 'Unknown',
            'isp': 'Unknown',
            'org': 'Unknown',
            'as': 'Unknown',
            'timezone': 'Unknown',
            'lat': 0,
            'lon': 0,
        }
    
    def get_country_flag(self, country_code: str) -> str:
        """Get flag emoji for country code"""
        if not country_code or len(country_code) != 2:
            return '🏳️'
        try:
            return chr(ord('🇦') + ord(country_code[0].upper()) - ord('A')) + \
                   chr(ord('🇦') + ord(country_code[1].upper()) - ord('A'))
        except:
            return '🏳️'
    
    async def check_proxy_http(self, proxy_info: Dict[str, Any]) -> Tuple[bool, Optional[str], float]:
        """Check HTTP/HTTPS proxy"""
        proxy_url = proxy_info['formatted']
        
        start_time = time.time()
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(
                    'https://api.ipify.org?format=json',
                    proxy=proxy_url
                ) as resp:
                    elapsed = time.time() - start_time
                    if resp.status == 200:
                        data = await resp.json()
                        return True, data.get('ip'), elapsed
        except Exception as e:
            pass
        
        elapsed = time.time() - start_time
        return False, None, elapsed
    
    async def check_proxy_socks(self, proxy_info: Dict[str, Any]) -> Tuple[bool, Optional[str], float]:
        """Check SOCKS4/SOCKS5 proxy using aiohttp-socks if available"""
        try:
            from aiohttp_socks import ProxyConnector, ProxyType
            
            proxy_type = ProxyType.SOCKS5 if proxy_info['type'] == 'socks5' else ProxyType.SOCKS4
            
            connector = ProxyConnector(
                proxy_type=proxy_type,
                host=proxy_info['host'],
                port=proxy_info['port'],
                username=proxy_info.get('username'),
                password=proxy_info.get('password'),
            )
            
            start_time = time.time()
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get('https://api.ipify.org?format=json') as resp:
                    elapsed = time.time() - start_time
                    if resp.status == 200:
                        data = await resp.json()
                        return True, data.get('ip'), elapsed
        except ImportError:
            return await self.check_proxy_http(proxy_info)
        except Exception as e:
            pass
        
        return False, None, time.time() - start_time if 'start_time' in locals() else 0
    
    async def check_proxy(self, proxy_string: str) -> Dict[str, Any]:
        """Main function to check a proxy - supports all types"""
        start_time = time.time()
        
        proxy_info = self.parse_proxy(proxy_string)
        
        if proxy_info['type'] in ['socks4', 'socks5']:
            is_alive, proxy_ip, response_time = await self.check_proxy_socks(proxy_info)
        else:
            is_alive, proxy_ip, response_time = await self.check_proxy_http(proxy_info)
        
        result = {
            'success': is_alive,
            'proxy': proxy_string,
            'type': proxy_info['type'].upper(),
            'host': proxy_info['host'],
            'port': proxy_info['port'],
            'has_auth': bool(proxy_info.get('username')),
            'response_time': round(response_time, 2),
            'proxy_ip': proxy_ip,
            'geo': None,
            'anonymity': 'Unknown',
            'is_rotating': False,
        }
        
        if is_alive and proxy_ip:
            geo_info = await self.get_geo_info(proxy_ip)
            result['geo'] = geo_info
            
            own_ip = await self.get_own_ip()
            if own_ip:
                if own_ip != proxy_ip:
                    result['anonymity'] = 'Elite/Anonymous'
                else:
                    result['anonymity'] = 'Transparent'
            
            if 'rotating' in proxy_string.lower() or 'residential' in proxy_string.lower():
                result['is_rotating'] = True
        
        result['total_time'] = round(time.time() - start_time, 2)
        
        return result
    
    def format_result_message(self, result: Dict[str, Any]) -> str:
        """Format the check result into a Telegram message"""
        if not result['success']:
            return (
                "╔═══════════════════════════════╗\n"
                "   ❌ 𝗣𝗥𝗢𝗫𝗬 𝗗𝗘𝗔𝗗\n"
                "╚═══════════════════════════════╝\n\n"
                f"🔌 <b>Proxy:</b> <code>{result['proxy'][:50]}{'...' if len(result['proxy']) > 50 else ''}</code>\n"
                f"📡 <b>Type:</b> {result['type']}\n"
                f"🌐 <b>Host:</b> {result['host']}\n"
                f"🔢 <b>Port:</b> {result['port']}\n"
                f"🔐 <b>Auth:</b> {'Yes' if result['has_auth'] else 'No'}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ <b>Status:</b> Connection Failed\n"
                f"⏱️ <b>Time:</b> {result['total_time']}s\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
        
        geo = result.get('geo', {})
        flag = self.get_country_flag(geo.get('country_code', 'XX'))
        
        rotating_badge = "🔄 ROTATING" if result['is_rotating'] else "📍 STATIC"
        
        speed_indicator = "🟢 Fast" if result['response_time'] < 2 else "🟡 Medium" if result['response_time'] < 5 else "🔴 Slow"
        
        return (
            "╔═══════════════════════════════╗\n"
            "   ✅ 𝗣𝗥𝗢𝗫𝗬 𝗔𝗟𝗜𝗩𝗘\n"
            "╚═══════════════════════════════╝\n\n"
            f"🔌 <b>Proxy:</b> <code>{result['proxy'][:50]}{'...' if len(result['proxy']) > 50 else ''}</code>\n"
            f"📡 <b>Type:</b> {result['type']} | {rotating_badge}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 <b>Proxy IP:</b> <code>{result['proxy_ip']}</code>\n"
            f"🔐 <b>Anonymity:</b> {result['anonymity']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{flag} <b>Country:</b> {geo.get('country', 'Unknown')}\n"
            f"🏙️ <b>City:</b> {geo.get('city', 'Unknown')}\n"
            f"📍 <b>Region:</b> {geo.get('region', 'Unknown')}\n"
            f"🏢 <b>ISP:</b> {geo.get('isp', 'Unknown')[:30]}...\n"
            f"🌍 <b>Timezone:</b> {geo.get('timezone', 'Unknown')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <b>Speed:</b> {speed_indicator} ({result['response_time']}s)\n"
            f"⏱️ <b>Total Time:</b> {result['total_time']}s\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "𝐃𝐄𝐕 : @MUMIRU"
        )


async def check_proxy(proxy_string: str) -> Dict[str, Any]:
    """Main function to check a proxy"""
    checker = ProxyChecker()
    return await checker.check_proxy(proxy_string)


def format_proxy_result(result: Dict[str, Any]) -> str:
    """Format proxy check result for Telegram"""
    checker = ProxyChecker()
    return checker.format_result_message(result)
