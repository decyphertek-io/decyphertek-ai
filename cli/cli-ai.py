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
        
        # Registry URLs
        self.workers_registry_url = "https://raw.githubusercontent.com/decyphertek-io/agent-store/main/workers.json"
        self.skills_registry_url = "https://raw.githubusercontent.com/decyphertek-io/mcp-store/main/skills.json"
        
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
    ▸ TYPE 'help' TO LIST COMMANDS | 'exit' TO QUIT
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
        if not self.password_file.exists():
            self.first_run_setup()
        
        # Authenticate user
        if not self.authenticate():
            print(f"\n{Colors.BLUE}[SYSTEM]{Colors.RESET} Authentication failed. Exiting.\n")
            sys.exit(1)
        
        # Download Adminotaur agent if not present
        if not self.adminotaur_agent_path.exists():
            self.download_adminotaur()
        
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
        print(f"{Colors.GREEN}[AI]{Colors.RESET} Processing: {user_input}")
    
    def first_run_setup(self):
        """First-run setup: create directories, password, SSH key"""
        print(f"\n{Colors.BLUE}[SYSTEM]{Colors.RESET} First run detected. Setting up Decyphertek AI...\n")
        
        # Create directories
        self.app_dir.mkdir(exist_ok=True)
        self.creds_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        self.agent_store_dir.mkdir(exist_ok=True)
        self.mcp_store_dir.mkdir(exist_ok=True)
        self.app_store_dir.mkdir(exist_ok=True)
        self.adminotaur_dir.mkdir(exist_ok=True)
        self.keys_dir.mkdir(exist_ok=True)
        
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created working directory: {self.app_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created credentials directory: {self.creds_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created agent store directory: {self.agent_store_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created MCP store directory: {self.mcp_store_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created app store directory: {self.app_store_dir}")
        print(f"{Colors.GREEN}[✓]{Colors.RESET} Created keys directory: {self.keys_dir}")
        
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
