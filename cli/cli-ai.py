#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import getpass
import argparse
import subprocess
import urllib.request
import readline
import glob
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent
    return base_path / relative_path


class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


class DecyphertekCLI:
    def __init__(self):
        self.version = "0.1.0"
        self.home_dir = Path.home()
        self.current_dir = str(self.home_dir)
        self.app_dir = self.home_dir / ".decyphertek.ai"
        self.creds_dir = self.app_dir / "creds"
        self.config_dir = self.app_dir / "config"
        self.agent_store_dir = self.app_dir / "agent-store"
        self.mcp_store_dir = self.app_dir / "mcp-store"
        self.app_store_dir = self.app_dir / "app-store"
        self.keys_dir = self.app_dir / "keys"
        self.ssh_key_path = self.keys_dir / "decyphertek.ai"
        self.password_file = self.app_dir / ".password_hash"
        
        # Configs directory in user home
        self.configs_dir = self.app_dir / "configs"
        self.ai_config_path = self.configs_dir / "ai-config.json"
        self.slash_commands_path = self.configs_dir / "slash-commands.json"
        
        # Registry URLs
        self.workers_registry_url = "https://raw.githubusercontent.com/decyphertek-io/agent-store/main/workers.json"
        self.skills_registry_url = "https://raw.githubusercontent.com/decyphertek-io/mcp-store/main/skills.json"
        self.configs_base_url = "https://raw.githubusercontent.com/decyphertek-io/decyphertek-ai/main/cli/configs/"
        
        # Registry paths
        self.workers_registry_path = self.agent_store_dir / "workers.json"
        self.skills_registry_path = self.mcp_store_dir / "skills.json"
        
        # Adminotaur paths
        self.adminotaur_dir = self.agent_store_dir / "adminotaur"
        self.adminotaur_agent_path = self.adminotaur_dir / "adminotaur.agent"
        self.adminotaur_md_path = self.adminotaur_dir / "adminotaur.md"
        
    def show_banner(self):
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║                  {Colors.GREEN}D E C Y P H E R T E K . A I{Colors.CYAN}                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.RESET}
{Colors.BLUE}    ▸ SYSADMIN AI ASSISTANT v{self.version}
    ▸ MODULAR AGENT/MCP ARCHITECTURE
    ▸ TYPE '/chat <msg>' FOR AI | '/help' FOR COMMANDS | 'exit' TO QUIT
{Colors.RESET}
"""
        print(banner)
        
    def run(self):
        parser = argparse.ArgumentParser(
            description="Decyphertek AI - Sysadmin AI Assistant",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        parser.add_argument(
            "--version",
            action="version",
            version=f"Decyphertek AI v{self.version}"
        )
        parser.add_argument(
            "command",
            nargs="?",
            help="Command to execute"
        )
        
        args = parser.parse_args()
        
        # Show banner first
        self.show_banner()
        
        # Check if first run
        is_first_run = not self.password_file.exists()
        if is_first_run:
            self.first_run_setup()
        
        # Authenticate user (skip if just completed first-run setup)
        if not is_first_run:
            if not self.authenticate():
                print(f"\n{Colors.BLUE}[SYSTEM]{Colors.RESET} Authentication failed. Exiting.\n")
                sys.exit(1)
        
        # Check for missing credentials
        self.check_credentials()
        
        if args.command:
            self.execute_command(args.command)
        else:
            self.interactive_mode()
    
    def execute_command(self, command):
        print(f"{Colors.GREEN}[EXEC]{Colors.RESET} {command}")
        
    def interactive_mode(self):
        # Setup tab completion
        readline.set_completer_delims(' \t\n')
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)
        
        while True:
            try:
                # Show current directory in prompt
                display_dir = self.current_dir.replace(str(self.home_dir), '~')
                prompt = f"\001{Colors.GREEN}\002decyphertek.ai\001{Colors.RESET}\002:\001{Colors.BLUE}\002{display_dir}\001{Colors.RESET}\002$ "
                user_input = input(prompt).strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print(f"\n{Colors.BLUE}[SYSTEM]{Colors.RESET} Exiting Decyphertek.ai\n")
                    break
                    
                if not user_input:
                    continue
                    
                self.process_input(user_input)
                
            except KeyboardInterrupt:
                print(f"\n\n{Colors.BLUE}[SYSTEM]{Colors.RESET} Exiting Decyphertek.ai\n")
                break
            except EOFError:
                break
    
    def _completer(self, text, state):
        """Tab completion for paths and slash commands"""
        try:
            line = readline.get_line_buffer()
            
            # Complete slash commands
            if line.startswith('/'):
                commands = ['/chat ', '/help', '/status', '/config', '/health']
                matches = [cmd for cmd in commands if cmd.startswith(line)]
                if state < len(matches):
                    return matches[state]
                return None
            
            # Complete file/directory paths
            if not text:
                text = ''
            
            # Handle ~ expansion
            if text.startswith('~'):
                text = str(Path.home()) + text[1:]
            
            # Get absolute path for completion
            if text.startswith('/'):
                search_path = text
            else:
                search_path = os.path.join(self.current_dir, text)
            
            # Find matches
            matches = glob.glob(search_path + '*')
            
            # Convert back to relative paths if needed
            if not text.startswith('/'):
                matches = [os.path.relpath(m, self.current_dir) for m in matches]
            
            # Add trailing slash for directories
            matches = [m + '/' if os.path.isdir(os.path.join(self.current_dir, m) if not m.startswith('/') else m) else m for m in matches]
            
            if state < len(matches):
                return matches[state]
            return None
        except:
            return None
    
    def process_input(self, user_input):
        """Process user input and route to appropriate handler"""
        
        # Handle slash commands
        if user_input.startswith('/'):
            command = user_input.split()[0].lower()
            
            if command == '/help':
                self.show_help()
            elif command == '/status':
                self.show_status()
            elif command == '/config':
                self.show_config()
            elif command == '/health':
                self.show_health()
            elif command == '/chat':
                # Extract message after /chat
                message = user_input[5:].strip()
                if message:
                    self.call_adminotaur(message)
                else:
                    print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Usage: /chat <your message>")
            else:
                print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Unknown command: {command}")
                print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Type /help for available commands")
        else:
            # Execute as Linux shell command
            self.execute_shell_command(user_input)
    
    def execute_shell_command(self, command):
        """Execute a shell command and display output"""
        try:
            # Handle cd command specially to maintain directory state
            if command.strip().startswith('cd '):
                new_dir = command.strip()[3:].strip()
                if not new_dir:
                    self.current_dir = str(self.home_dir)
                else:
                    # Expand ~ and resolve path
                    if new_dir.startswith('~'):
                        new_dir = str(Path.home() / new_dir[2:].lstrip('/'))
                    elif not new_dir.startswith('/'):
                        new_dir = str(Path(self.current_dir) / new_dir)
                    
                    # Check if directory exists
                    if Path(new_dir).is_dir():
                        self.current_dir = str(Path(new_dir).resolve())
                    else:
                        print(f"{Colors.BLUE}[ERROR]{Colors.RESET} cd: {new_dir}: No such file or directory")
                return
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.current_dir
            )
            
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(f"{Colors.BLUE}{result.stderr}{Colors.RESET}", end='')
            
            if result.returncode != 0 and not result.stderr:
                print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Command exited with code {result.returncode}")
        
        except subprocess.TimeoutExpired:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Command timed out")
        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to execute command: {e}")
    
    def call_adminotaur(self, user_input):
        """Call Adminotaur agent with user input"""
        try:
            if not self.adminotaur_agent_path.exists():
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Adminotaur agent not found. Downloading...")
                self.download_adminotaur()
            
            # Call Adminotaur agent executable with user input
            result = subprocess.run(
                [str(self.adminotaur_agent_path), user_input],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}[AI]{Colors.RESET} {result.stdout}")
            else:
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Adminotaur failed: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Adminotaur timed out")
        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to call Adminotaur: {e}")
    
    def show_help(self):
        """Show available commands"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}Available Commands:{Colors.RESET}\n")
        print(f"{Colors.GREEN}/chat <message>{Colors.RESET}  - Chat with AI assistant")
        print(f"{Colors.GREEN}/help{Colors.RESET}            - Show this help message")
        print(f"{Colors.GREEN}/status{Colors.RESET}          - Show system status")
        print(f"{Colors.GREEN}/config{Colors.RESET}          - Show configuration")
        print(f"{Colors.GREEN}/health{Colors.RESET}          - Check MCP Gateway and skill connectivity")
        print(f"{Colors.GREEN}exit{Colors.RESET}             - Exit application")
        print(f"\n{Colors.CYAN}Note:{Colors.RESET} Regular commands are executed as shell commands\n")
    
    def show_health(self):
        """Check MCP Gateway and skill connectivity"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}MCP Health Check:{Colors.RESET}\n")
        
        # Test Adminotaur agent
        print(f"{Colors.CYAN}Testing Adminotaur Agent:{Colors.RESET}")
        adminotaur_path = self.app_dir / "agent-store" / "adminotaur" / "adminotaur.agent"
        if adminotaur_path.exists():
            try:
                result = subprocess.run(
                    [str(adminotaur_path), "/status"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"{Colors.GREEN}[✓]{Colors.RESET} Adminotaur agent is callable")
                else:
                    print(f"{Colors.RED}[✗]{Colors.RESET} Adminotaur agent failed")
                    print(f"    Error: {result.stderr[:100]}")
            except Exception as e:
                print(f"{Colors.RED}[✗]{Colors.RESET} Adminotaur agent error: {str(e)}")
        else:
            print(f"{Colors.RED}[✗]{Colors.RESET} Adminotaur agent not found at {adminotaur_path}")
        
        # Test MCP Gateway connectivity
        print(f"\n{Colors.CYAN}Testing MCP Gateway:{Colors.RESET}")
        gateway_running = False
        try:
            import urllib.request
            url = "http://localhost:9000/health"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    print(f"{Colors.GREEN}[✓]{Colors.RESET} MCP Gateway is running at localhost:9000")
                    gateway_running = True
                else:
                    print(f"{Colors.YELLOW}[⚠]{Colors.RESET} MCP Gateway responded with status {response.getcode()}")
        except Exception as e:
            print(f"{Colors.RED}[✗]{Colors.RESET} MCP Gateway not reachable at localhost:9000")
            print(f"    Error: {str(e)}")
            print(f"    {Colors.YELLOW}Hint:{Colors.RESET} Start MCP Gateway with: mcp-gateway.py")
        
        # Test MCP skills if gateway is running
        if gateway_running:
            print(f"\n{Colors.CYAN}Testing MCP Skills:{Colors.RESET}")
            mcp_store = self.app_dir / "mcp-store"
            if mcp_store.exists():
                skills = [item.name for item in mcp_store.iterdir() if item.is_dir()]
                if skills:
                    for skill in skills:
                        try:
                            # Send dummy test request to each skill
                            test_request = {
                                "skill": skill,
                                "tool": "health" if skill == "mcp-gateway" else "test",
                                "params": {}
                            }
                            url = "http://localhost:9000/invoke"
                            req = urllib.request.Request(
                                url,
                                data=json.dumps(test_request).encode('utf-8'),
                                headers={'Content-Type': 'application/json'}
                            )
                            with urllib.request.urlopen(req, timeout=10) as response:
                                result = json.loads(response.read().decode('utf-8'))
                                # Check if we got any response (even error is OK for connectivity test)
                                print(f"{Colors.GREEN}[✓]{Colors.RESET} {skill}: Reachable")
                        except Exception as e:
                            print(f"{Colors.RED}[✗]{Colors.RESET} {skill}: {str(e)[:60]}")
                else:
                    print(f"  {Colors.YELLOW}No skills found in mcp-store{Colors.RESET}")
            else:
                print(f"  {Colors.RED}MCP store directory not found{Colors.RESET}")
        
        print()
    
    def show_status(self):
        """Show system status"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}System Status:{Colors.RESET}\n")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Working directory: {self.app_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Credentials directory: {self.creds_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Configs directory: {self.configs_dir}")
        
        # Check for encrypted credentials
        if self.creds_dir.exists():
            creds = list(self.creds_dir.glob("*.enc"))
            print(f"{Colors.GREEN}[✓]{Colors.RESET} Stored credentials: {len(creds)}")
            for cred in creds:
                print(f"  - {cred.stem}")
        print()
    
    def show_config(self):
        """Show configuration"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}Configuration:{Colors.RESET}\n")
        
        if self.ai_config_path.exists():
            try:
                config = json.loads(self.ai_config_path.read_text())
                print(f"{Colors.GREEN}AI Config:{Colors.RESET}")
                print(f"  Default Provider: {config.get('default_provider', 'N/A')}")
                print(f"  Providers: {', '.join(config.get('providers', {}).keys())}")
            except:
                print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to load ai-config.json")
        else:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} ai-config.json not found")
        print()
    
    def first_run_setup(self):
        """First-run setup: create directories, password, SSH key"""
        print(f"\n{Colors.BLUE}[SYSTEM]{Colors.RESET} First run detected. Setting up Decyphertek AI...\n")
        
        # Create directories
        self.app_dir.mkdir(exist_ok=True)
        self.creds_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        self.configs_dir.mkdir(exist_ok=True)
        self.agent_store_dir.mkdir(exist_ok=True)
        self.mcp_store_dir.mkdir(exist_ok=True)
        self.app_store_dir.mkdir(exist_ok=True)
        self.adminotaur_dir.mkdir(exist_ok=True)
        self.keys_dir.mkdir(exist_ok=True)
        
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created working directory: {self.app_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created credentials directory: {self.creds_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created configs directory: {self.configs_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created agent store directory: {self.agent_store_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created MCP store directory: {self.mcp_store_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created app store directory: {self.app_store_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created keys directory: {self.keys_dir}")
        
        # Download config files
        print(f"\n{Colors.BLUE}[SETUP]{Colors.RESET} Downloading configuration files...")
        self.download_configs()
        
        # Set password
        print(f"\n{Colors.BLUE}[SETUP]{Colors.RESET} Set a master password to protect the application:")
        while True:
            password = getpass.getpass("Enter password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password == confirm and len(password) >= 8:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                self.password_file.write_text(password_hash)
                self.password_file.chmod(0o600)
                print(f"{Colors.GREEN}[✓]{Colors.RESET} Password set successfully")
                break
            elif len(password) < 8:
                print(f"{Colors.BLUE}[SETUP]{Colors.RESET} Password must be at least 8 characters")
            else:
                print(f"{Colors.BLUE}[SETUP]{Colors.RESET} Passwords don't match. Try again.")
        
        # Generate SSH key for credential encryption
        print(f"\n{Colors.BLUE}[SETUP]{Colors.RESET} Generating SSH key for credential encryption...")
        if not self.ssh_key_path.exists():
            try:
                subprocess.run([
                    "ssh-keygen",
                    "-t", "rsa",
                    "-b", "4096",
                    "-f", str(self.ssh_key_path),
                    "-N", "",
                    "-C", "decyphertek.ai-credential-encryption"
                ], check=True, capture_output=True)
                print(f"{Colors.GREEN}[✓]{Colors.RESET} SSH key generated: {self.ssh_key_path}")
                print(f"{Colors.GREEN}[✓]{Colors.RESET} Public key: {self.ssh_key_path}.pub")
                print()
            except subprocess.CalledProcessError as e:
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to generate SSH key: {e}")
                sys.exit(1)
        
        # Download all enabled agents, skills, and apps (only on first run)
        self.download_all_stores()
    
    def authenticate(self):
        """Authenticate user with password"""
        stored_hash = self.password_file.read_text().strip()
        print(f"\n{Colors.CYAN}{Colors.BOLD}=== DECYPHERTEK.AI LOGIN ==={Colors.RESET}\n")
        
        for attempt in range(3):
            password = getpass.getpass(f"{Colors.BLUE}[LOGIN]{Colors.RESET} Enter password: ")
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if password_hash == stored_hash:
                print(f"{Colors.GREEN}[✓]{Colors.RESET} Authentication successful\n")
                return True
            else:
                remaining = 2 - attempt
                if remaining > 0:
                    print(f"{Colors.BLUE}[LOGIN]{Colors.RESET} Incorrect password. {remaining} attempts remaining.")
        
        return False
    
    def check_credentials(self):
        """Check ai-config.json and prompt for missing credentials"""
        if not self.ai_config_path.exists():
            return
        
        try:
            ai_config = json.loads(self.ai_config_path.read_text())
            providers = ai_config.get("providers", {})
            
            for provider_id, provider_config in providers.items():
                if not provider_config.get("enabled", False):
                    continue
                
                credential_service = provider_config.get("credential_service")
                if not credential_service:
                    continue
                
                cred_file = self.creds_dir / f"{credential_service}.enc"
                
                if not cred_file.exists():
                    print(f"\n{Colors.BLUE}[SETUP]{Colors.RESET} {provider_config.get('name', provider_id)} is enabled but no API key found.")
                    print(f"{Colors.BLUE}[SETUP]{Colors.RESET} Please enter your API key to continue.\n")
                    
                    api_key = getpass.getpass(f"Enter {provider_config.get('name', provider_id)} API key: ").strip()
                    
                    if api_key:
                        self.store_credential(credential_service, api_key)
                        print(f"{Colors.GREEN}[✓]{Colors.RESET} API key stored and encrypted\n")
                    else:
                        print(f"{Colors.BLUE}[WARNING]{Colors.RESET} No API key provided. AI features may not work.\n")
        
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Error checking credentials: {e}")
    
    def store_credential(self, service: str, credential: str):
        """Encrypt and store a credential"""
        try:
            # SSH key path is /path/to/decyphertek.ai, public key is /path/to/decyphertek.ai.pub
            ssh_pub_key_path = Path(str(self.ssh_key_path) + ".pub")
            openssl_pub_key_path = self.keys_dir / "decyphertek.ai.pem"
            
            # Check if SSH public key exists
            if not ssh_pub_key_path.exists():
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} SSH public key not found: {ssh_pub_key_path}")
                return False
            
            # Convert SSH public key to OpenSSL PEM format
            convert_result = subprocess.run(
                ["ssh-keygen", "-f", str(ssh_pub_key_path), "-e", "-m", "PKCS8"],
                capture_output=True,
                text=True
            )
            
            if convert_result.returncode != 0:
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to convert SSH key")
                print(f"{Colors.BLUE}[DEBUG]{Colors.RESET} stderr: {convert_result.stderr}")
                return False
            
            openssl_pub_key_path.write_text(convert_result.stdout)
            
            # Encrypt credential with OpenSSL public key
            result = subprocess.run(
                ["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", str(openssl_pub_key_path)],
                input=credential.encode(),
                capture_output=True,
                text=False
            )
            
            if result.returncode != 0:
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Encryption failed")
                print(f"{Colors.BLUE}[DEBUG]{Colors.RESET} stderr: {result.stderr.decode()}")
                return False
            
            cred_file = self.creds_dir / f"{service}.enc"
            cred_file.write_bytes(result.stdout)
            cred_file.chmod(0o600)
            return True
        
        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to store credential: {e}")
            return False
    
    def download_configs(self):
        """Download config files from GitHub"""
        config_files = ["ai-config.json", "slash-commands.json"]
        
        for config_file in config_files:
            try:
                url = self.configs_base_url + config_file
                with urllib.request.urlopen(url) as response:
                    config_data = response.read()
                    (self.configs_dir / config_file).write_bytes(config_data)
                    print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded {config_file}")
            except Exception as e:
                print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download {config_file}: {e}")
    
    def download_workers_registry(self):
        """Download workers.json registry from agent-store"""
        try:
            with urllib.request.urlopen(self.workers_registry_url) as response:
                registry_data = response.read()
                self.workers_registry_path.write_bytes(registry_data)
                return True
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download workers registry: {e}")
            return False
    
    def download_skills_registry(self):
        """Download skills.json registry from mcp-store"""
        try:
            with urllib.request.urlopen(self.skills_registry_url) as response:
                registry_data = response.read()
                self.skills_registry_path.write_bytes(registry_data)
                return True
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download skills registry: {e}")
            return False
    
    def download_all_stores(self):
        """Download all enabled items from agent-store, mcp-store, and app-store"""
        print(f"\n{Colors.BLUE}[SYSTEM]{Colors.RESET} Downloading enabled agents, skills, and apps...\n")
        
        # Download agent-store items
        if self.download_workers_registry():
            self.download_enabled_agents()
        
        # Download mcp-store items
        if self.download_skills_registry():
            self.download_enabled_skills()
        
        # Download app-store items
        self.download_enabled_apps()
    
    def download_enabled_agents(self):
        """Download all enabled agents from workers.json"""
        try:
            registry = json.loads(self.workers_registry_path.read_text())
            agents = registry.get("agents", {})
            
            for agent_id, agent_config in agents.items():
                if not agent_config.get("enabled", False):
                    continue
                
                agent_dir = self.agent_store_dir / agent_id
                agent_dir.mkdir(exist_ok=True)
                
                repo_url = agent_config.get("repo_url", "")
                folder_path = agent_config.get("folder_path", "")
                files = agent_config.get("files", {})
                
                if not repo_url or not folder_path:
                    continue
                
                raw_base = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/" + folder_path
                
                # Download agent executable
                if "agent" in files:
                    agent_path = agent_dir / files["agent"].split("/")[-1]
                    try:
                        with urllib.request.urlopen(raw_base + files["agent"]) as response:
                            agent_path.write_bytes(response.read())
                            agent_path.chmod(0o755)
                            print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded agent: {agent_id}")
                    except Exception as e:
                        print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download {agent_id}: {e}")
                
                # Download docs
                if "docs" in files:
                    docs_path = agent_dir / files["docs"].split("/")[-1]
                    try:
                        with urllib.request.urlopen(raw_base + files["docs"]) as response:
                            docs_path.write_bytes(response.read())
                    except:
                        pass
        
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Error downloading agents: {e}")
    
    def download_enabled_skills(self):
        """Download all enabled MCP skills from skills.json"""
        try:
            registry = json.loads(self.skills_registry_path.read_text())
            skills = registry.get("skills", {})
            
            for skill_id, skill_config in skills.items():
                if not skill_config.get("enabled", False):
                    continue
                
                skill_dir = self.mcp_store_dir / skill_id
                skill_dir.mkdir(exist_ok=True)
                
                repo_url = skill_config.get("repo_url", "")
                folder_path = skill_config.get("folder_path", "")
                files = skill_config.get("files", {})
                
                if not repo_url or not folder_path:
                    continue
                
                raw_base = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/" + folder_path
                
                # Download skill executable
                if "executable" in files:
                    skill_path = skill_dir / files["executable"].split("/")[-1]
                    try:
                        with urllib.request.urlopen(raw_base + files["executable"]) as response:
                            skill_path.write_bytes(response.read())
                            skill_path.chmod(0o755)
                            print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded skill: {skill_id}")
                    except Exception as e:
                        print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download {skill_id}: {e}")
                
                # Download config and docs
                for file_type in ["config", "docs"]:
                    if file_type in files:
                        file_path = skill_dir / files[file_type].split("/")[-1]
                        try:
                            with urllib.request.urlopen(raw_base + files[file_type]) as response:
                                file_path.write_bytes(response.read())
                        except:
                            pass
        
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Error downloading skills: {e}")
    
    def download_enabled_apps(self):
        """Download all enabled apps from app.json"""
        try:
            app_registry_url = "https://raw.githubusercontent.com/decyphertek-io/app-store/main/app.json"
            
            with urllib.request.urlopen(app_registry_url) as response:
                registry = json.loads(response.read())
            
            apps = registry.get("apps", {})
            
            for app_id, app_config in apps.items():
                if not app_config.get("enabled", False):
                    continue
                
                app_dir = self.app_store_dir / app_id
                app_dir.mkdir(exist_ok=True)
                
                repo_url = app_config.get("repo_url", "")
                folder_path = app_config.get("folder_path", "")
                files = app_config.get("files", {})
                
                if not repo_url or not folder_path:
                    continue
                
                raw_base = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/" + folder_path
                
                # Download app executable
                if "executable" in files:
                    app_path = app_dir / files["executable"].split("/")[-1]
                    try:
                        with urllib.request.urlopen(raw_base + files["executable"]) as response:
                            app_path.write_bytes(response.read())
                            app_path.chmod(0o755)
                            print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded app: {app_id}")
                    except Exception as e:
                        print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download {app_id}: {e}")
                
                # Download config and docs
                for file_type in ["config", "docs"]:
                    if file_type in files:
                        file_path = app_dir / files[file_type].split("/")[-1]
                        try:
                            with urllib.request.urlopen(raw_base + files[file_type]) as response:
                                file_path.write_bytes(response.read())
                        except:
                            pass
        
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Error downloading apps: {e}")
    
    def download_adminotaur(self):
        """Download Adminotaur agent using workers.json registry"""
        print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Downloading agent registry...")
        
        # Download workers.json first
        if not self.download_workers_registry():
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Could not download workers registry")
            return
        
        # Parse workers.json to get adminotaur config
        try:
            registry_data = json.loads(self.workers_registry_path.read_text())
            adminotaur_config = registry_data.get("agents", {}).get("adminotaur", {})
            repo_url = adminotaur_config.get("repo_url", "")
            folder_path = adminotaur_config.get("folder_path", "")
            files = adminotaur_config.get("files", {})
            
            if not repo_url or not folder_path or not files:
                print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Invalid registry format")
                return
            
            # Convert GitHub URL to raw URL base
            raw_base = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/" + folder_path
            
            print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Downloading Adminotaur agent...")
            
            # Download agent executable
            if "agent" in files:
                agent_url = raw_base + files["agent"]
                with urllib.request.urlopen(agent_url) as response:
                    agent_data = response.read()
                    self.adminotaur_agent_path.write_bytes(agent_data)
                    self.adminotaur_agent_path.chmod(0o755)  # Make executable
                    print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded: {files['agent']}")
            
            # Download docs
            if "docs" in files:
                docs_url = raw_base + files["docs"]
                try:
                    with urllib.request.urlopen(docs_url) as response:
                        docs_data = response.read()
                        self.adminotaur_md_path.write_bytes(docs_data)
                        print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded: {files['docs']}")
                except Exception as e:
                    print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Could not download {files['docs']}: {e}")
                
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download Adminotaur: {e}")
    
    def encrypt_credential(self, credential):
        """Encrypt credential using SSH public key"""
        with open(f"{self.ssh_key_path}.pub", 'rb') as key_file:
            public_key = serialization.load_ssh_public_key(
                key_file.read(),
                backend=default_backend()
            )
        
        encrypted = public_key.encrypt(
            credential.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode()
    
    def decrypt_credential(self, encrypted_credential):
        """Decrypt credential using SSH private key"""
        with open(self.ssh_key_path, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        
        encrypted_bytes = base64.b64decode(encrypted_credential)
        decrypted = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode()


def main():
    cli = DecyphertekCLI()
    cli.run()


if __name__ == "__main__":
    main()
