import asyncio
import sys
from advanced_hotmail_checker import AdvancedHotmailChecker, AccountDetails
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

async def demo():
    console.print(Panel.fit(
        "[bold cyan]ADVANCED HOTMAIL/OUTLOOK ACCOUNT CHECKER - DEMO MODE[/bold cyan]\n"
        "[yellow]This is a demonstration of the tool's capabilities[/yellow]",
        box=box.DOUBLE,
        border_style="cyan"
    ))
    
    console.print("\n[bold]Tool Features:[/bold]")
    console.print("✓ Full account data capture (name, country, birthdate)")
    console.print("✓ Email statistics (unread/total messages, folder counts)")
    console.print("✓ OAuth and refresh token extraction")
    console.print("✓ Payment information capture (balance, methods, orders)")
    console.print("✓ Multi-threaded async checking")
    console.print("✓ Proxy rotation support")
    console.print("✓ Automatic retry logic")
    console.print("✓ Beautiful rich terminal output")
    console.print("✓ Multiple output formats (TXT, JSON)")
    
    console.print("\n[bold]Supported Account Statuses:[/bold]")
    console.print("[green]SUCCESS[/green] - Valid credentials, full data captured")
    console.print("[yellow]2FACTOR[/yellow] - Valid but requires 2FA")
    console.print("[red]INVALID_EMAIL[/red] - Account doesn't exist")
    console.print("[red]INVALID_PASSWORD[/red] - Wrong password")
    console.print("[blue]TIMEOUT[/blue] - Connection timeout")
    console.print("[red]ERROR[/red] - Other errors")
    
    console.print("\n[bold]Captured Data Includes:[/bold]")
    console.print("• Email & password")
    console.print("• Display name, country, birthdate")
    console.print("• Unread messages count")
    console.print("• Total messages count")
    console.print("• Inbox/Sent/Draft/Deleted counts")
    console.print("• Session cookies")
    console.print("• OAuth access & refresh tokens")
    console.print("• Account balance")
    console.print("• Payment methods")
    console.print("• PayPal email")
    console.print("• Total orders count")
    
    console.print("\n[bold cyan]To Use the Tool:[/bold cyan]")
    console.print("1. Prepare a combos.txt file (email:password format)")
    console.print("2. Optionally prepare a proxies.txt file")
    console.print("3. Run: [bold]python advanced_hotmail_checker.py[/bold]")
    console.print("4. Follow the interactive prompts")
    console.print("5. Check the results/ folder for output")
    
    console.print("\n[yellow]Example combo file format:[/yellow]")
    console.print("user1@outlook.com:password123")
    console.print("user2@hotmail.com:mypass456")
    console.print("user3@live.com:secret789")
    
    console.print("\n[yellow]Example proxy file format:[/yellow]")
    console.print("http://proxy1.com:8080")
    console.print("http://user:pass@proxy2.com:3128")
    console.print("socks5://proxy3.com:1080")
    
    console.print("\n[bold green]✓ Tool is ready to use![/bold green]")
    console.print("[dim]Note: Only use on accounts you own or have permission to test.[/dim]\n")

if __name__ == "__main__":
    asyncio.run(demo())
