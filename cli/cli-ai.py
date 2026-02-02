#!/usr/bin/env python3
import sys
import argparse
import os
import json
import hashlib
import getpass
import subprocess
import urllib.request
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
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


class DecyphertekCLI:
    def __init__(self):
        self.version = "0.1.0"
        self.home_dir = Path.home()
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
    ▸ TYPE '/help' TO LIST COMMANDS | 'exit' TO QUIT
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
        
        # Download Adminotaur agent if not present
        if not self.adminotaur_agent_path.exists():
            self.download_adminotaur()
        
        # Check for missing credentials
        self.check_credentials()
        
        if args.command:
            self.execute_command(args.command)
        else:
            self.interactive_mode()
    
    def execute_command(self, command):
        print(f"{Colors.GREEN}[EXEC]{Colors.RESET} {command}")
        
    def interactive_mode(self):
        while True:
            try:
                user_input = input(f"{Colors.CYAN}┌─[{Colors.GREEN}decyphertek.ai{Colors.CYAN}]\n└──▸{Colors.RESET} ").strip()
                
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
            else:
                print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Unknown command: {command}")
                print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Type /help for available commands")
        else:
            # Route to Adminotaur agent
            print(f"{Colors.GREEN}[AI]{Colors.RESET} Processing: {user_input}")
            print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Adminotaur agent not yet implemented")
    
    def show_help(self):
        """Show available commands"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}Available Commands:{Colors.RESET}\n")
        print(f"{Colors.GREEN}/help{Colors.RESET}     - Show this help message")
        print(f"{Colors.GREEN}/status{Colors.RESET}   - Show system status")
        print(f"{Colors.GREEN}/config{Colors.RESET}   - Show configuration")
        print(f"{Colors.GREEN}exit{Colors.RESET}      - Exit application\n")
    
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
            except subprocess.CalledProcessError as e:
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to generate SSH key: {e}")
                sys.exit(1)
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}[✓] Setup complete!{Colors.RESET}\n")
    
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
