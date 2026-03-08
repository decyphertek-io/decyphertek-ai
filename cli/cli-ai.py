
#!/usr/bin/env python3
import os
import sys
import json
import yaml
import hashlib
import getpass
import argparse
import subprocess
import urllib.request
import readline
import glob
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
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
        self.salt_path = self.keys_dir / "salt.bin"
        self.password_file = self.app_dir / ".password_hash"
        self._fernet: Fernet = None  # set after authenticate()
        
        # Configs directory in user home
        self.configs_dir = self.app_dir / "configs"
        self.ai_config_path = self.configs_dir / "ai-config.yaml"
        self.slash_commands_path = self.configs_dir / "slash-commands.yaml"
        
        # Registry URLs
        self.workers_registry_url = "https://raw.githubusercontent.com/decyphertek-io/agent-store/main/workers.yaml"
        self.skills_registry_url = "https://raw.githubusercontent.com/decyphertek-io/mcp-store/main/skills.yaml"
        self.configs_base_url = "https://raw.githubusercontent.com/decyphertek-io/decyphertek-ai/main/cli/configs/"
        
        # Registry paths
        self.workers_registry_path = self.agent_store_dir / "workers.yaml"
        self.skills_registry_path = self.mcp_store_dir / "skills.yaml"
        
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
        readline.set_completer_delims(' \n;|&')
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
    
    def _get_path_executables(self):
        """Return all executable names found in $PATH directories (cached)."""
        if not hasattr(self, '_path_executables_cache'):
            execs = set()
            for d in os.environ.get('PATH', '').split(':'):
                try:
                    for f in os.listdir(d):
                        fp = os.path.join(d, f)
                        if os.access(fp, os.X_OK) and os.path.isfile(fp):
                            execs.add(f)
                except OSError:
                    pass
            self._path_executables_cache = sorted(execs)
        return self._path_executables_cache

    def _completer(self, text, state):
        """Tab completion for paths, shell commands, and slash commands"""
        try:
            line = readline.get_line_buffer()
            
            # Complete slash commands
            if line.startswith('/') and not os.path.exists(line.split()[0]):
                commands = ['/build agent', '/build mcp', '/chat ', '/code ', '/help', '/status', '/config', '/health', '/settings', '/web ', '/rag ', '/news ']
                # Also add dynamic slash commands from slash-commands.yaml
                try:
                    if self.slash_commands_path.exists():
                        slash_config = yaml.safe_load(self.slash_commands_path.read_text())
                        for cmd in slash_config.get("commands", {}).keys():
                            commands.append(cmd + ' ')
                except Exception:
                    pass
                matches = [cmd for cmd in commands if cmd.startswith(line)]
                if state < len(matches):
                    return matches[state]
                return None
            
            # If we're completing the first word (command name), complete from PATH
            tokens = line.split()
            completing_command = len(tokens) == 0 or (len(tokens) == 1 and not line.endswith(' '))
            if completing_command and not text.startswith('.') and not text.startswith('/') and not text.startswith('~'):
                execs = self._get_path_executables()
                matches = [e for e in execs if e.startswith(text)]
                if state < len(matches):
                    return matches[state]
                return None
            
            # Complete file/directory paths
            if not text:
                text = ''
            
            # Handle ~ expansion
            orig_text = text
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
            if not orig_text.startswith('/') and not orig_text.startswith('~'):
                matches = [os.path.relpath(m, self.current_dir) for m in matches]
            
            # Add trailing slash for directories
            matches = [m + '/' if os.path.isdir(os.path.join(self.current_dir, m) if not m.startswith('/') else m) else m for m in matches]
            
            if state < len(matches):
                return matches[state]
            return None
        except Exception:
            return None
    
    def process_input(self, user_input):
        """Process user input and route to appropriate handler"""
        
        # Handle slash commands
        if user_input.startswith('/'):
            command = user_input.split()[0].lower()
            
            if command == '/build':
                parts = user_input.split(None, 2)
                subcommand = parts[1].lower() if len(parts) > 1 else ''
                if subcommand == 'agent':
                    self.build_agent()
                elif subcommand == 'mcp':
                    self.build_mcp()
                else:
                    print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Usage: /build agent  or  /build mcp")
                return
            elif command == '/help':
                self.show_help()
                return
            elif command == '/status':
                self.show_status()
                return
            elif command == '/config':
                self.show_config()
                return
            elif command == '/health':
                self.show_health()
                return
            elif command == '/settings':
                self.show_settings()
                return
            elif command == '/chat':
                # Extract message after /chat
                message = user_input[5:].strip()
                if message:
                    self.call_adminotaur(message)
                else:
                    print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Usage: /chat <your message>")
                return
            elif command == '/code':
                # Extract coding instruction after /code — routes to Adminotaur with file system tools
                message = user_input[5:].strip()
                if message:
                    self.call_adminotaur(message)
                else:
                    print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Usage: /code <instruction>")
                    print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Example: /code create ~/Downloads/hello.txt with content 'Hello World'")
                return
            else:
                # Check if it's an MCP skill command from slash-commands.yaml
                try:
                    if self.slash_commands_path.exists():
                        slash_config = yaml.safe_load(self.slash_commands_path.read_text())
                        commands = slash_config.get("commands", {})
                        
                        if command in commands:
                            cmd_config = commands[command]
                            if cmd_config.get("enabled", True) and "mcp_skill" in cmd_config:
                                # Extract the query after the command
                                parts = user_input.split(None, 1)
                                query = parts[1] if len(parts) > 1 else ""
                                if not query:
                                    print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Usage: {command} <query>")
                                    return
                                self.call_mcp_skill(cmd_config, query)
                                return
                except Exception as e:
                    print(f"{Colors.BLUE}[DEBUG]{Colors.RESET} Exception in MCP routing: {e}")
                    import traceback
                    traceback.print_exc()
                
                print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Unknown command: {command}")
                print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Type /help for available commands")
        else:
            # Execute as Linux shell command
            self.execute_shell_command(user_input)
    
    def _prompt(self, question: str) -> str:
        """Prompt the user for input, restoring readline after."""
        try:
            print(f"{Colors.CYAN}{question}{Colors.RESET} ", end="", flush=True)
            return input("").strip()
        except (KeyboardInterrupt, EOFError):
            return ""

    def _build_agent_env(self) -> dict:
        """Build an environment dict with decrypted OpenRouter credentials injected."""
        env = os.environ.copy()
        env["DECYPHERTEK_CONFIGS_DIR"]    = str(self.configs_dir)
        env["DECYPHERTEK_AI_CONFIG"]      = str(self.ai_config_path)
        env["DECYPHERTEK_SLASH_COMMANDS"] = str(self.slash_commands_path)
        env["DECYPHERTEK_MCP_STORE"]      = str(self.mcp_store_dir)
        env["DECYPHERTEK_AGENT_STORE"]    = str(self.agent_store_dir)
        try:
            openrouter_cred = self.creds_dir / "openrouter.enc"
            if openrouter_cred.exists():
                key = self.decrypt_credential("openrouter")
                if key:
                    env["OPENROUTER_API_KEY"] = key
            if self.ai_config_path.exists():
                ai_config = yaml.safe_load(self.ai_config_path.read_text())
                provider = ai_config.get("providers", {}).get("openrouter-ai", {})
                if provider.get("default_model"):
                    env["OPENROUTER_MODEL"] = provider["default_model"]
                if provider.get("base_url"):
                    env["OPENROUTER_BASE_URL"] = provider["base_url"]
        except Exception:
            pass
        return env

    def _run_builder_in_background(self, agent_path: str, spec: dict, label: str):
        """Run a builder agent binary in a background thread, print result when done."""
        import threading
        import json as _json

        env = self._build_agent_env()

        def _run():
            try:
                if not Path(agent_path).exists():
                    print(f"\n{Colors.BLUE}[{label}]{Colors.RESET} Builder not found: {agent_path}")
                    print(f"{Colors.BLUE}[{label}]{Colors.RESET} Download it with: /settings → Download agents")
                    return
                result = subprocess.run(
                    [agent_path],
                    input=_json.dumps(spec),
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env=env,
                )
                output = result.stdout.strip() or result.stderr.strip()
                print(f"\n{Colors.GREEN}[{label} DONE]{Colors.RESET} {output}\n", flush=True)
                print(f"{Colors.CYAN}decyphertek.ai:~${Colors.RESET} ", end="", flush=True)
            except subprocess.TimeoutExpired:
                print(f"\n{Colors.BLUE}[{label}]{Colors.RESET} Timed out after 5 minutes\n")
            except Exception as e:
                print(f"\n{Colors.BLUE}[{label}]{Colors.RESET} Error: {e}\n")

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        print(f"{Colors.BLUE}[{label}]{Colors.RESET} Running in background — you can keep working...")

    def build_agent(self):
        """Interactive /build agent flow"""
        print(f"\n{Colors.CYAN}=== Build Agent ==={Colors.RESET}")
        name = self._prompt("Agent name?")
        if not name:
            print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Cancelled.")
            return
        purpose = self._prompt("What should this agent do?")
        if not purpose:
            print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Cancelled.")
            return
        tools = self._prompt("What tools/skills does it need?")
        apis = self._prompt("Any external APIs or API keys needed?")

        spec = {
            "name": name.lower().replace(" ", "-"),
            "purpose": purpose,
            "tools": tools,
            "apis": apis,
        }

        agent_path = str(self.agent_store_dir / "agent-builder" / "agent-builder.agent")
        self._run_builder_in_background(agent_path, spec, "agent-builder")

    def build_mcp(self):
        """Interactive /build mcp flow"""
        print(f"\n{Colors.CYAN}=== Build MCP Skill ==={Colors.RESET}")
        name = self._prompt("Skill name?")
        if not name:
            print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Cancelled.")
            return
        purpose = self._prompt("What should this skill do?")
        if not purpose:
            print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Cancelled.")
            return
        api = self._prompt("What API does it call?")
        api_keys = self._prompt("Any API keys needed?")

        spec = {
            "name": name.lower().replace(" ", "-"),
            "purpose": purpose,
            "api": api,
            "api_keys": api_keys,
        }

        agent_path = str(self.agent_store_dir / "mcp-builder" / "mcp-builder.agent")
        self._run_builder_in_background(agent_path, spec, "mcp-builder")

    # Commands that require a full interactive TTY (no output capture)
    _INTERACTIVE_COMMANDS = {
        'vim', 'vi', 'nano', 'emacs', 'less', 'more', 'man', 'top', 'htop',
        'ssh', 'ftp', 'sftp', 'telnet', 'mysql', 'psql', 'python', 'python3',
        'ipython', 'node', 'irb', 'bash', 'sh', 'zsh', 'fish', 'watch',
        'screen', 'tmux', 'mc', 'ranger', 'ncdu', 'cmus', 'mutt',
    }

    def execute_shell_command(self, command):
        """Execute a shell command and display output"""
        try:
            # Handle cd command specially to maintain directory state
            stripped = command.strip()
            if stripped == 'cd' or stripped.startswith('cd ') or stripped.startswith('cd\t'):
                new_dir = stripped[2:].strip() if len(stripped) > 2 else ''
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

            # Determine if the command is interactive (needs a real TTY)
            base_cmd = stripped.split()[0] if stripped.split() else ''
            is_interactive = base_cmd in self._INTERACTIVE_COMMANDS

            if is_interactive:
                # Run interactively — inherit stdin/stdout/stderr so the full
                # terminal UI works (cursor movement, colour, input, etc.)
                subprocess.run(
                    command,
                    shell=True,
                    cwd=self.current_dir,
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.current_dir
                )
                
                if result.stdout:
                    print(result.stdout, end='')
                if result.stderr:
                    print(result.stderr, end='')
                
                if result.returncode != 0 and not result.stdout and not result.stderr:
                    print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Command exited with code {result.returncode}")
        
        except subprocess.TimeoutExpired:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Command timed out after 60 seconds")
        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to execute command: {e}")

    def _find_mcp_executable(self, skill_dir: Path, skill_id: str) -> Path | None:
        """Find the MCP executable in a skill directory, trying multiple patterns."""
        # Try exact name patterns in order of preference
        candidates = [
            skill_dir / f"{skill_id}.mcp",
            skill_dir / f"{skill_id.split('-')[0]}.mcp",
        ]
        # Also glob for any .mcp file
        candidates += list(skill_dir.glob("*.mcp"))

        for candidate in candidates:
            if candidate.exists() and os.access(candidate, os.X_OK):
                return candidate

        # Try any executable file in the directory as a last resort
        for f in skill_dir.iterdir():
            if f.is_file() and os.access(f, os.X_OK):
                return f

        return None

    def call_mcp_skill(self, cmd_config: dict, query: str):
        """
        Directly invoke an MCP skill executable with the user query,
        then pass the result to Adminotaur (or print it directly).
        """
        skill_name = cmd_config.get("mcp_skill", "")
        skill_dir = self.mcp_store_dir / skill_name

        if not skill_dir.exists():
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} MCP skill directory not found: {skill_dir}")
            print(f"{Colors.BLUE}[INFO]{Colors.RESET}  Run /status to check installed skills.")
            return

        executable = self._find_mcp_executable(skill_dir, skill_name)
        if not executable:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} No executable found in {skill_dir}")
            return

        # Build environment with decrypted credentials (OpenRouter key + config paths included)
        env = self._build_agent_env()

        # Decrypt skill credentials if available
        if self.skills_registry_path.exists():
            try:
                skills_config = yaml.safe_load(self.skills_registry_path.read_text())
                skill_info = skills_config.get("skills", {}).get(skill_name, {})
                credential = skill_info.get("credentials")
                env_var = skill_info.get("env_mapping")

                if credential and env_var:
                    cred_file = self.creds_dir / f"{credential}.enc"
                    if cred_file.exists():
                        decrypted_key = self.decrypt_credential(credential)
                        if decrypted_key:
                            env[env_var] = decrypted_key
                    else:
                        print(f"\n{Colors.YELLOW}[WARNING]{Colors.RESET} No API key found for '{credential}'.")
                        try:
                            answer = input(f"Would you like to add one now? (Y/n): ").strip().lower()
                        except (EOFError, KeyboardInterrupt):
                            answer = "n"
                        if answer in ("", "y", "yes"):
                            try:
                                import getpass as _getpass
                                api_key = _getpass.getpass(f"Enter API key for '{credential}': ").strip()
                                if api_key:
                                    if self.store_credential(credential, api_key):
                                        env[env_var] = api_key
                                        print(f"{Colors.GREEN}[✓]{Colors.RESET} API key stored and will be used now.\n")
                                    else:
                                        print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} Failed to store API key. Continuing without it.\n")
                                else:
                                    print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} No key entered. Continuing without it.\n")
                            except Exception as _e:
                                print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} Could not store key: {_e}\n")
                        else:
                            print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} Skipping. Skill may not work without an API key.\n")
            except Exception as e:
                print(f"{Colors.BLUE}[DEBUG]{Colors.RESET} Error loading skill credentials: {e}")

        # Also inject the OpenRouter API key so the skill can call the AI provider
        try:
            openrouter_cred = self.creds_dir / "openrouter.enc"
            if openrouter_cred.exists():
                openrouter_key = self.decrypt_credential("openrouter")
                if openrouter_key:
                    env["OPENROUTER_API_KEY"] = openrouter_key

            # Pass the preferred model from ai-config.yaml
            if self.ai_config_path.exists():
                ai_config = yaml.safe_load(self.ai_config_path.read_text())
                model = (ai_config.get("providers", {})
                                  .get("openrouter-ai", {})
                                  .get("default_model", ""))
                if model:
                    env["OPENROUTER_MODEL"] = model
                base_url = (ai_config.get("providers", {})
                                     .get("openrouter-ai", {})
                                     .get("base_url", ""))
                if base_url:
                    env["OPENROUTER_BASE_URL"] = base_url
        except Exception as e:
            print(f"{Colors.BLUE}[DEBUG]{Colors.RESET} Error injecting OpenRouter key: {e}")

        print(f"{Colors.CYAN}[MCP]{Colors.RESET} Running skill '{skill_name}' ...")

        try:
            result = subprocess.run(
                [str(executable), query],
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    # Pipe MCP skill output through Adminotaur for AI summarization
                    summarization_prompt = (
                        f"The user asked: {query}\n\n"
                        f"Here are the raw results from the {skill_name} skill:\n\n"
                        f"{output}\n\n"
                        f"Please provide a helpful, concise summary of these results."
                    )
                    self.call_adminotaur(summarization_prompt)
                else:
                    print(f"{Colors.BLUE}[INFO]{Colors.RESET} Skill returned no output.")
            else:
                print(f"{Colors.RED}[ERROR]{Colors.RESET} Skill '{skill_name}' failed (exit {result.returncode}):")
                if result.stderr:
                    print(f"  {result.stderr.strip()}")
                if result.stdout:
                    print(f"  stdout: {result.stdout.strip()}")

        except subprocess.TimeoutExpired:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Skill '{skill_name}' timed out after 60s")
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to run skill '{skill_name}': {e}")

    def start_mcp_server(self, skill_name):
        """Start MCP server on-demand with decrypted API keys"""
        try:
            # Get MCP server path
            mcp_path = self.mcp_store_dir / skill_name
            
            executable = self._find_mcp_executable(mcp_path, skill_name)
            if not executable:
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} No executable found for skill: {skill_name}")
                return None
            
            # Build environment with OpenRouter key + config paths already included
            env = self._build_agent_env()

            # Dynamically decrypt MCP skill credentials from skills.yaml
            if self.skills_registry_path.exists():
                skills_config = yaml.safe_load(self.skills_registry_path.read_text())
                skill_info = skills_config.get("skills", {}).get(skill_name, {})
                credential = skill_info.get("credentials")
                env_var = skill_info.get("env_mapping")
                
                if credential:
                    cred_file = self.creds_dir / f"{credential}.enc"
                    if cred_file.exists():
                        decrypted_key = self.decrypt_credential(credential)
                        if decrypted_key and env_var:
                            env[env_var] = decrypted_key
            
            # Start MCP server process
            process = subprocess.Popen(
                [str(executable)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            
            return process
        
        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to start MCP server {skill_name}: {e}")
            return None
    
    def call_adminotaur(self, user_input):
        """Call Adminotaur agent with user input"""
        mcp_process = None
        try:
            adminotaur_path = self.agent_store_dir / "adminotaur" / "adminotaur.agent"
            
            if not adminotaur_path.exists():
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Adminotaur agent not found at {adminotaur_path}")
                return
            
            env = os.environ.copy()

            # Pass config paths explicitly so Adminotaur can find yaml configs
            # (Adminotaur may default to .json — these env vars let it use .yaml)
            env["DECYPHERTEK_CONFIGS_DIR"] = str(self.configs_dir)
            env["DECYPHERTEK_AI_CONFIG"] = str(self.ai_config_path)
            env["DECYPHERTEK_SLASH_COMMANDS"] = str(self.slash_commands_path)
            env["DECYPHERTEK_MCP_STORE"] = str(self.mcp_store_dir)
            env["DECYPHERTEK_AGENT_STORE"] = str(self.agent_store_dir)
            env["DECYPHERTEK_WORKERS_REGISTRY"] = str(self.workers_registry_path)
            env["DECYPHERTEK_SKILLS_REGISTRY"] = str(self.skills_registry_path)
            
            # Dynamically decrypt agent credentials from workers.yaml
            if self.workers_registry_path.exists():
                workers_config = yaml.safe_load(self.workers_registry_path.read_text())
                agent_info = workers_config.get("agents", {}).get("adminotaur", {})
                credential = agent_info.get("credentials")
                env_var = agent_info.get("env_mapping")
                
                if credential:
                    cred_file = self.creds_dir / f"{credential}.enc"
                    if cred_file.exists():
                        decrypted_key = self.decrypt_credential(credential)
                        if decrypted_key and env_var:
                            env[env_var] = decrypted_key

            # Always inject OpenRouter key and model for /chat usage
            try:
                openrouter_cred = self.creds_dir / "openrouter.enc"
                if openrouter_cred.exists():
                    openrouter_key = self.decrypt_credential("openrouter")
                    if openrouter_key:
                        env["OPENROUTER_API_KEY"] = openrouter_key

                if self.ai_config_path.exists():
                    ai_config = yaml.safe_load(self.ai_config_path.read_text())
                    model = (ai_config.get("providers", {})
                                      .get("openrouter-ai", {})
                                      .get("default_model", ""))
                    if model:
                        env["OPENROUTER_MODEL"] = model
                    base_url = (ai_config.get("providers", {})
                                         .get("openrouter-ai", {})
                                         .get("base_url", ""))
                    if base_url:
                        env["OPENROUTER_BASE_URL"] = base_url
            except Exception as e:
                print(f"{Colors.BLUE}[DEBUG]{Colors.RESET} Error injecting OpenRouter key: {e}")
            
            # Call Adminotaur with user input via stdin to avoid ARG_MAX limits on large payloads
            # (e.g. MCP skill output piped as a summarization prompt can exceed ~2MB argv limit)
            # stdout/stderr pass through directly so the user sees live progress
            result = subprocess.run(
                [str(adminotaur_path), "--stdin"],
                input=user_input,
                env=env,
                text=True,
            )
            
            if result.returncode != 0:
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Adminotaur exited with code {result.returncode}")
        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to call Adminotaur: {e}")
    
    def show_help(self):
        """Show available commands"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}Available Commands:{Colors.RESET}\n")
        print(f"{Colors.GREEN}/chat <message>{Colors.RESET}  - Chat with AI assistant")
        print(f"{Colors.GREEN}/code <instruction>{Colors.RESET} - AI coding agent: write/read/edit files and run shell commands")
        print(f"{Colors.GREEN}/help{Colors.RESET}            - Show this help message")
        print(f"{Colors.GREEN}/status{Colors.RESET}          - Show system status")
        print(f"{Colors.GREEN}/config{Colors.RESET}          - Show configuration")
        print(f"{Colors.GREEN}/health{Colors.RESET}          - Check system health and connectivity")
        print(f"{Colors.GREEN}/settings{Colors.RESET}        - Interactive settings menu")
        
        # Dynamically load MCP slash commands from slash-commands.yaml
        try:
            if self.slash_commands_path.exists():
                slash_config = yaml.safe_load(self.slash_commands_path.read_text())
                commands = slash_config.get("commands", {})
                
                # Filter for MCP skill commands only (not builtin)
                mcp_commands = {cmd: cfg for cmd, cfg in commands.items() 
                               if "mcp_skill" in cfg and cfg.get("enabled", True)}
                
                if mcp_commands:
                    print(f"\n{Colors.CYAN}{Colors.BOLD}MCP Skills:{Colors.RESET}\n")
                    for cmd, cfg in sorted(mcp_commands.items()):
                        description = cfg.get("description", f"Use {cfg.get('mcp_skill')} skill")
                        print(f"{Colors.GREEN}{cmd} <query>{Colors.RESET}  - {description}")
        except Exception as e:
            pass
        
        print(f"\n{Colors.GREEN}exit{Colors.RESET}             - Exit application")
        print(f"\n{Colors.CYAN}Note:{Colors.RESET} Regular commands are executed as shell commands\n")
    
    def show_settings(self):
        """Interactive settings menu"""
        while True:
            print(f"\n{Colors.CYAN}{Colors.BOLD}Settings Menu:{Colors.RESET}\n")
            print(f"{Colors.GREEN}1.{Colors.RESET} Manage Agents (add/remove)")
            print(f"{Colors.GREEN}2.{Colors.RESET} Manage MCP Skills (add/remove)")
            print(f"{Colors.GREEN}3.{Colors.RESET} Manage Apps (add/remove)")
            print(f"{Colors.GREEN}4.{Colors.RESET} Manage API Keys")
            print(f"{Colors.GREEN}5.{Colors.RESET} Change OpenRouter Model")
            print(f"{Colors.GREEN}6.{Colors.RESET} Back to main")

            print(f"\n{Colors.CYAN}Select option (1-6):{Colors.RESET}", end=" ")
            choice = input().strip()

            if choice == '1':
                self._manage_agents()
            elif choice == '2':
                self._manage_mcp_skills()
            elif choice == '3':
                self._manage_apps()
            elif choice == '4':
                self._manage_api_keys()
            elif choice == '5':
                self._change_model()
            elif choice == '6':
                break
            else:
                print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Invalid option")
    
    # Required items that cannot be removed
    REQUIRED_AGENTS = {"adminotaur"}
    REQUIRED_APPS = {"chromadb"}

    def _manage_agents(self):
        """Add or remove agents from the agent store"""
        try:
            if not self.workers_registry_path.exists():
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} workers.yaml not found")
                return

            registry = yaml.safe_load(self.workers_registry_path.read_text())
            agents = registry.get("agents", {})

            while True:
                print(f"\n{Colors.CYAN}{Colors.BOLD}Agents:{Colors.RESET}\n")
                agent_list = list(agents.items())
                for idx, (agent_id, agent_config) in enumerate(agent_list, 1):
                    installed = (self.agent_store_dir / agent_id / agent_config.get("executable", "")).exists()
                    required = agent_id in self.REQUIRED_AGENTS
                    status = f"{Colors.GREEN}[INSTALLED]{Colors.RESET}" if installed else f"{Colors.RED}[NOT INSTALLED]{Colors.RESET}"
                    lock = f" {Colors.YELLOW}[REQUIRED]{Colors.RESET}" if required else ""
                    print(f"{idx}. {agent_id} {status}{lock}")

                print(f"\n{Colors.CYAN}Enter agent number to install/remove, or 0 to go back:{Colors.RESET}")
                choice = input("> ").strip()
                if choice == '0':
                    break
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(agent_list):
                        agent_id, agent_config = agent_list[idx]
                        if agent_id in self.REQUIRED_AGENTS:
                            print(f"{Colors.YELLOW}[PROTECTED]{Colors.RESET} {agent_id} is required and cannot be removed")
                            continue
                        agent_path = self.agent_store_dir / agent_id / agent_config.get("executable", "")
                        if agent_path.exists():
                            agent_path.unlink()
                            print(f"{Colors.GREEN}[✓]{Colors.RESET} Removed {agent_id}")
                        else:
                            # Download it
                            release_url = agent_config.get("release_url", "")
                            if release_url:
                                agent_path.parent.mkdir(parents=True, exist_ok=True)
                                try:
                                    with urllib.request.urlopen(release_url) as response:
                                        agent_path.write_bytes(response.read())
                                        agent_path.chmod(0o755)
                                    print(f"{Colors.GREEN}[✓]{Colors.RESET} Installed {agent_id}")
                                except Exception as e:
                                    print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to download {agent_id}: {e}")
                    else:
                        print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Invalid number")
                except ValueError:
                    print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Invalid input")

        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to manage agents: {e}")

    def _manage_apps(self):
        """Add or remove apps from the app store"""
        try:
            app_registry_url = "https://raw.githubusercontent.com/decyphertek-io/app-store/main/app.yaml"
            try:
                with urllib.request.urlopen(app_registry_url) as response:
                    registry = yaml.safe_load(response.read())
            except Exception as e:
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Could not fetch app registry: {e}")
                return

            apps = registry.get("apps", {})

            while True:
                print(f"\n{Colors.CYAN}{Colors.BOLD}Apps:{Colors.RESET}\n")
                app_list = list(apps.items())
                for idx, (app_id, app_config) in enumerate(app_list, 1):
                    installed = (self.app_store_dir / app_id).exists() and any((self.app_store_dir / app_id).iterdir())
                    required = app_id in self.REQUIRED_APPS
                    status = f"{Colors.GREEN}[INSTALLED]{Colors.RESET}" if installed else f"{Colors.RED}[NOT INSTALLED]{Colors.RESET}"
                    lock = f" {Colors.YELLOW}[REQUIRED]{Colors.RESET}" if required else ""
                    print(f"{idx}. {app_id} {status}{lock}")

                print(f"\n{Colors.CYAN}Enter app number to install/remove, or 0 to go back:{Colors.RESET}")
                choice = input("> ").strip()
                if choice == '0':
                    break
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(app_list):
                        app_id, app_config = app_list[idx]
                        if app_id in self.REQUIRED_APPS:
                            print(f"{Colors.YELLOW}[PROTECTED]{Colors.RESET} {app_id} is required for memory and cannot be removed")
                            continue
                        app_dir = self.app_store_dir / app_id
                        if app_dir.exists() and any(app_dir.iterdir()):
                            import shutil
                            shutil.rmtree(app_dir)
                            print(f"{Colors.GREEN}[✓]{Colors.RESET} Removed {app_id}")
                        else:
                            # Download it
                            repo_url = app_config.get("repo_url", "")
                            folder_path = app_config.get("folder_path", "")
                            executable = app_config.get("executable", "")
                            if repo_url and folder_path and executable:
                                raw_base = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/" + folder_path
                                app_dir.mkdir(parents=True, exist_ok=True)
                                app_path = app_dir / executable.split("/")[-1]
                                try:
                                    with urllib.request.urlopen(raw_base + executable) as response:
                                        app_path.write_bytes(response.read())
                                        app_path.chmod(0o755)
                                    print(f"{Colors.GREEN}[✓]{Colors.RESET} Installed {app_id}")
                                except Exception as e:
                                    print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to download {app_id}: {e}")
                    else:
                        print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Invalid number")
                except ValueError:
                    print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Invalid input")

        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to manage apps: {e}")

    def _manage_mcp_skills(self):
        """Add or remove MCP skills"""
        try:
            if not self.skills_registry_path.exists():
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} skills.yaml not found")
                return

            registry = yaml.safe_load(self.skills_registry_path.read_text())
            skills = registry.get("skills", {})

            while True:
                print(f"\n{Colors.CYAN}{Colors.BOLD}MCP Skills:{Colors.RESET}\n")
                skill_list = list(skills.items())
                for idx, (skill_id, skill_config) in enumerate(skill_list, 1):
                    skill_dir = self.mcp_store_dir / skill_id
                    installed = skill_dir.exists() and any(skill_dir.glob("*.mcp"))
                    status = f"{Colors.GREEN}[INSTALLED]{Colors.RESET}" if installed else f"{Colors.RED}[NOT INSTALLED]{Colors.RESET}"
                    print(f"{idx}. {skill_id} {status}")

                print(f"\n{Colors.CYAN}Enter skill number to install/remove, or 0 to go back:{Colors.RESET}")
                choice = input("> ").strip()
                if choice == '0':
                    break
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(skill_list):
                        skill_id, skill_config = skill_list[idx]
                        skill_dir = self.mcp_store_dir / skill_id
                        installed = skill_dir.exists() and any(skill_dir.glob("*.mcp"))
                        if installed:
                            import shutil
                            shutil.rmtree(skill_dir)
                            print(f"{Colors.GREEN}[✓]{Colors.RESET} Removed {skill_id}")
                        else:
                            repo_url = skill_config.get("repo_url", "")
                            folder_path = skill_config.get("folder_path", "")
                            executable = skill_config.get("executable", "")
                            release_url = skill_config.get("release_url", "")
                            if release_url or (repo_url and folder_path and executable):
                                skill_dir.mkdir(parents=True, exist_ok=True)
                                if release_url:
                                    skill_url = release_url
                                else:
                                    raw_base = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/" + folder_path
                                    skill_url = raw_base + executable
                                skill_path = skill_dir / (executable or "skill").split("/")[-1]
                                try:
                                    with urllib.request.urlopen(skill_url) as response:
                                        skill_path.write_bytes(response.read())
                                        skill_path.chmod(0o755)
                                    print(f"{Colors.GREEN}[✓]{Colors.RESET} Installed {skill_id}")
                                except Exception as e:
                                    print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to download {skill_id}: {e}")
                    else:
                        print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Invalid number")
                except ValueError:
                    print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Invalid input")

        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to manage skills: {e}")
    
    def _manage_api_keys(self):
        """Manage API keys"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}API Key Management:{Colors.RESET}\n")
        print(f"{Colors.GREEN}1.{Colors.RESET} Add/Update OpenRouter API Key")
        print(f"{Colors.GREEN}2.{Colors.RESET} Add/Update World News API Key")
        print(f"{Colors.GREEN}3.{Colors.RESET} View stored credentials")
        print(f"{Colors.GREEN}4.{Colors.RESET} Back")
        
        print(f"\n{Colors.CYAN}Select option (1-4):{Colors.RESET}", end=" ")
        choice = input().strip()
        
        if choice == '1':
            print(f"{Colors.CYAN}Enter OpenRouter API key:{Colors.RESET}", end=" ")
            api_key = getpass.getpass("")
            if api_key:
                if self.store_credential("openrouter", api_key):
                    print(f"{Colors.GREEN}[✓]{Colors.RESET} OpenRouter API key stored")
                else:
                    print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to store API key")
        elif choice == '2':
            print(f"{Colors.CYAN}Enter World News API key:{Colors.RESET}", end=" ")
            api_key = getpass.getpass("")
            if api_key:
                if self.store_credential("worldnews", api_key):
                    print(f"{Colors.GREEN}[✓]{Colors.RESET} World News API key stored")
                else:
                    print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to store API key")
        elif choice == '3':
            cred_files = list(self.creds_dir.glob("*.enc"))
            if cred_files:
                print(f"\n{Colors.CYAN}Stored credentials:{Colors.RESET}")
                for cred_file in cred_files:
                    service = cred_file.stem
                    print(f"  - {service}")
            else:
                print(f"{Colors.BLUE}[INFO]{Colors.RESET} No stored credentials")
    
    def _change_model(self):
        """Change OpenRouter model"""
        try:
            ai_config_path = self.configs_dir / "ai-config.yaml"
            if not ai_config_path.exists():
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} ai-config.yaml not found")
                return
            
            ai_config = yaml.safe_load(ai_config_path.read_text())
            current_model = ai_config.get("providers", {}).get("openrouter-ai", {}).get("default_model", "")
            
            print(f"\n{Colors.CYAN}{Colors.BOLD}Change OpenRouter Model:{Colors.RESET}\n")
            print(f"Current model: {Colors.GREEN}{current_model}{Colors.RESET}\n")
            print(f"{Colors.CYAN}Popular models:{Colors.RESET}")
            print(f"1. anthropic/claude-3.5-sonnet")
            print(f"2. anthropic/claude-3-opus")
            print(f"3. openai/gpt-4-turbo")
            print(f"4. openai/gpt-4o")
            print(f"5. meta-llama/llama-3.1-70b-instruct")
            print(f"6. deepseek/deepseek-r1-0528:free")
            print(f"7. Custom model")
            
            print(f"\n{Colors.CYAN}Select option (1-7):{Colors.RESET}", end=" ")
            choice = input().strip()
            
            models = {
                '1': 'anthropic/claude-3.5-sonnet',
                '2': 'anthropic/claude-3-opus',
                '3': 'openai/gpt-4-turbo',
                '4': 'openai/gpt-4o',
                '5': 'meta-llama/llama-3.1-70b-instruct',
                '6': 'deepseek/deepseek-r1-0528:free',
            }
            
            if choice in models:
                new_model = models[choice]
            elif choice == '7':
                print(f"{Colors.CYAN}Enter model name:{Colors.RESET}", end=" ")
                new_model = input().strip()
            else:
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Invalid option")
                return
            
            if new_model:
                ai_config["providers"]["openrouter-ai"]["default_model"] = new_model
                # Save back as YAML to preserve format
                ai_config_path.write_text(yaml.dump(ai_config, default_flow_style=False))
                print(f"{Colors.GREEN}[✓]{Colors.RESET} Model changed to: {new_model}")
        
        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to change model: {e}")
    
    def show_health(self):
        """Check system health and connectivity"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}System Health Check:{Colors.RESET}\n")

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

        # Test OpenRouter API key decryption
        print(f"\n{Colors.CYAN}Testing OpenRouter Credentials:{Colors.RESET}")
        try:
            cred_file = self.creds_dir / "openrouter.enc"
            if cred_file.exists():
                decrypted_key = self.decrypt_credential("openrouter")
                if decrypted_key and len(decrypted_key) > 0:
                    print(f"{Colors.GREEN}[✓]{Colors.RESET} OpenRouter API key decrypted successfully")
                else:
                    print(f"{Colors.RED}[✗]{Colors.RESET} API key decryption returned empty result")
            else:
                print(f"{Colors.RED}[✗]{Colors.RESET} OpenRouter credential file not found")
        except Exception as e:
            print(f"{Colors.RED}[✗]{Colors.RESET} Failed to decrypt API key: {str(e)}")
        
        # Test MCP skills
        print(f"\n{Colors.CYAN}Testing MCP Skills:{Colors.RESET}")
        mcp_store = self.app_dir / "mcp-store"
        if mcp_store.exists():
            skills = [item for item in mcp_store.iterdir()
                      if item.is_dir() and item.name not in ['mcp-gateway', 'openrouter-ai']]
            if skills:
                for skill_dir in skills:
                    executable = self._find_mcp_executable(skill_dir, skill_dir.name)
                    if executable:
                        print(f"{Colors.GREEN}[✓]{Colors.RESET} {skill_dir.name}: Executable found ({executable.name})")
                    else:
                        print(f"{Colors.RED}[✗]{Colors.RESET} {skill_dir.name}: No executable found in {skill_dir}")
            else:
                print(f"  {Colors.YELLOW}No active MCP skills found{Colors.RESET}")
        else:
            print(f"  {Colors.RED}MCP store directory not found{Colors.RESET}")

        # Test config files
        print(f"\n{Colors.CYAN}Testing Config Files:{Colors.RESET}")
        for config_name, config_path in [
            ("ai-config.yaml", self.ai_config_path),
            ("slash-commands.yaml", self.slash_commands_path),
            ("workers.yaml", self.workers_registry_path),
            ("skills.yaml", self.skills_registry_path),
        ]:
            if config_path.exists():
                print(f"{Colors.GREEN}[✓]{Colors.RESET} {config_name}: Found at {config_path}")
            else:
                print(f"{Colors.RED}[✗]{Colors.RESET} {config_name}: NOT found at {config_path}")

        print()
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

        # Show installed MCP skills
        print(f"\n{Colors.CYAN}Installed MCP Skills:{Colors.RESET}")
        if self.mcp_store_dir.exists():
            skills = [item for item in self.mcp_store_dir.iterdir()
                      if item.is_dir() and item.name not in ['mcp-gateway', 'openrouter-ai']]
            if skills:
                for skill_dir in skills:
                    executable = self._find_mcp_executable(skill_dir, skill_dir.name)
                    status = f"{Colors.GREEN}[ready]{Colors.RESET}" if executable else f"{Colors.RED}[no executable]{Colors.RESET}"
                    print(f"  {skill_dir.name} {status}")
            else:
                print(f"  {Colors.YELLOW}None installed{Colors.RESET}")
        else:
            print(f"  {Colors.RED}MCP store not found{Colors.RESET}")

        print()
    
    def show_config(self):
        """Show configuration"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}Configuration:{Colors.RESET}\n")
        
        if self.ai_config_path.exists():
            try:
                config = yaml.safe_load(self.ai_config_path.read_text())
                print(f"{Colors.GREEN}AI Config:{Colors.RESET}")
                print(f"  Default Provider: {config.get('default_provider', 'N/A')}")
                providers = config.get('providers', {})
                print(f"  Providers: {', '.join(providers.keys())}")
                for pid, pcfg in providers.items():
                    model = pcfg.get('default_model', 'N/A')
                    print(f"    {pid}: model={model}")
            except Exception as e:
                print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to load ai-config.yaml: {e}")
        else:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} ai-config.yaml not found at {self.ai_config_path}")

        if self.slash_commands_path.exists():
            try:
                slash_config = yaml.safe_load(self.slash_commands_path.read_text())
                commands = slash_config.get("commands", {})
                enabled_mcp = [cmd for cmd, cfg in commands.items() if "mcp_skill" in cfg and cfg.get("enabled", True)]
                print(f"\n{Colors.GREEN}Slash Commands Config:{Colors.RESET}")
                print(f"  MCP skill commands enabled: {', '.join(enabled_mcp) if enabled_mcp else 'none'}")
            except Exception as e:
                print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to load slash-commands.yaml: {e}")
        else:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} slash-commands.yaml not found at {self.slash_commands_path}")

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
        
        # Generate encryption salt for Fernet key derivation
        print(f"\n{Colors.BLUE}[SETUP]{Colors.RESET} Generating encryption salt...")
        if not self.salt_path.exists():
            self.keys_dir.mkdir(parents=True, exist_ok=True)
            salt = os.urandom(16)
            self.salt_path.write_bytes(salt)
            self.salt_path.chmod(0o600)
            print(f"{Colors.GREEN}[✓]{Colors.RESET} Encryption salt: {self.salt_path}")
            print()
        # Derive Fernet key from password so credentials can be stored immediately
        self._fernet = self._derive_fernet(password)
        
        # Download all enabled agents, skills, and apps (only on first run)
        self.download_all_stores()
    
    def _derive_fernet(self, password: str) -> Fernet:
        """Derive a Fernet key from the master password + stored salt"""
        salt = self.salt_path.read_bytes()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)

    def authenticate(self):
        """Authenticate user with password and derive encryption key"""
        stored_hash = self.password_file.read_text().strip()
        print(f"\n{Colors.CYAN}{Colors.BOLD}=== DECYPHERTEK.AI LOGIN ==={Colors.RESET}\n")
        
        for attempt in range(3):
            password = getpass.getpass(f"{Colors.BLUE}[LOGIN]{Colors.RESET} Enter password: ")
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if password_hash == stored_hash:
                self._fernet = self._derive_fernet(password)
                print(f"{Colors.GREEN}[✓]{Colors.RESET} Authentication successful\n")
                return True
            else:
                remaining = 2 - attempt
                if remaining > 0:
                    print(f"{Colors.BLUE}[LOGIN]{Colors.RESET} Incorrect password. {remaining} attempts remaining.")
        
        return False
    
    def check_credentials(self):
        """Check ai-config.yaml and prompt for missing credentials"""
        if not self.ai_config_path.exists():
            return
        
        try:
            ai_config = yaml.safe_load(self.ai_config_path.read_text())
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
        """Encrypt and store a credential using Fernet (AES-128)"""
        try:
            if self._fernet is None:
                print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Not authenticated — cannot encrypt credential")
                return False
            encrypted = self._fernet.encrypt(credential.encode())
            cred_file = self.creds_dir / f"{service}.enc"
            cred_file.write_bytes(encrypted)
            cred_file.chmod(0o600)
            return True
        except Exception as e:
            print(f"{Colors.BLUE}[ERROR]{Colors.RESET} Failed to store credential: {e}")
            return False
    
    def download_configs(self):
        """Download config files from GitHub"""
        config_files = ["ai-config.yaml", "slash-commands.yaml"]
        
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
        """Download workers.yaml registry from agent-store"""
        try:
            with urllib.request.urlopen(self.workers_registry_url) as response:
                registry_data = response.read()
                self.workers_registry_path.write_bytes(registry_data)
                return True
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download workers registry: {e}")
            return False
    
    def download_skills_registry(self):
        """Download skills.yaml registry from mcp-store"""
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
        """Download all enabled agents from workers.yaml"""
        try:
            registry = yaml.safe_load(self.workers_registry_path.read_text())
            agents = registry.get("agents", {})
            
            for agent_id, agent_config in agents.items():
                if not agent_config.get("enabled", False):
                    continue
                
                agent_dir = self.agent_store_dir / agent_id
                agent_dir.mkdir(exist_ok=True)
                
                repo_url = agent_config.get("repo_url", "")
                folder_path = agent_config.get("folder_path", "")
                executable = agent_config.get("executable", "")
                release_url = agent_config.get("release_url", "")
                
                if not repo_url or not folder_path or not executable:
                    continue
                
                # Use release_url if available, otherwise fall back to raw GitHub URL
                if release_url:
                    agent_url = release_url
                else:
                    raw_base = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/" + folder_path
                    agent_url = raw_base + executable
                
                # Download agent executable
                agent_path = agent_dir / executable.split("/")[-1]
                try:
                    with urllib.request.urlopen(agent_url) as response:
                        agent_path.write_bytes(response.read())
                        agent_path.chmod(0o755)
                        print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded agent: {agent_id}")
                except Exception as e:
                    print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download {agent_id}: {e}")
        
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Error downloading agents: {e}")
    
    def download_enabled_skills(self):
        """Download all enabled MCP skills from skills.yaml"""
        try:
            registry = yaml.safe_load(self.skills_registry_path.read_text())
            skills = registry.get("skills", {})
            
            for skill_id, skill_config in skills.items():
                if not skill_config.get("enabled", False):
                    continue
                
                skill_dir = self.mcp_store_dir / skill_id
                skill_dir.mkdir(exist_ok=True)
                
                repo_url = skill_config.get("repo_url", "")
                folder_path = skill_config.get("folder_path", "")
                executable = skill_config.get("executable", "")
                
                if not repo_url or not folder_path or not executable:
                    continue
                
                raw_base = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/" + folder_path
                
                # Download skill executable
                skill_path = skill_dir / executable.split("/")[-1]
                try:
                    with urllib.request.urlopen(raw_base + executable) as response:
                        skill_path.write_bytes(response.read())
                        skill_path.chmod(0o755)
                        print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded skill: {skill_id}")
                except Exception as e:
                    print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download {skill_id}: {e}")
        
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Error downloading skills: {e}")
    
    def download_enabled_apps(self):
        """Download only required apps (chromadb) on first run"""
        try:
            app_registry_url = "https://raw.githubusercontent.com/decyphertek-io/app-store/main/app.yaml"

            with urllib.request.urlopen(app_registry_url) as response:
                registry = yaml.safe_load(response.read())

            apps = registry.get("apps", {})

            for app_id, app_config in apps.items():
                # Only auto-download required apps on first run
                if app_id not in self.REQUIRED_APPS:
                    continue

                app_dir = self.app_store_dir / app_id
                app_dir.mkdir(exist_ok=True)

                repo_url = app_config.get("repo_url", "")
                folder_path = app_config.get("folder_path", "")
                executable = app_config.get("executable", "")
                config = app_config.get("config", "")
                config_path = app_config.get("config_path", "")

                if not repo_url or not folder_path or not executable:
                    continue

                raw_base = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/" + folder_path

                app_path = app_dir / executable.split("/")[-1]
                try:
                    with urllib.request.urlopen(raw_base + executable) as response:
                        app_path.write_bytes(response.read())
                        app_path.chmod(0o755)
                        print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded app: {app_id}")
                except Exception as e:
                    print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download {app_id}: {e}")

                if config and config_path:
                    config_dir = Path(config_path.replace("~", str(Path.home())))
                    config_dir.mkdir(parents=True, exist_ok=True)
                    config_file_path = config_dir / config
                    try:
                        with urllib.request.urlopen(raw_base + config) as response:
                            config_file_path.write_bytes(response.read())
                            print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded config: {config}")
                    except Exception:
                        pass

        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Error downloading apps: {e}")
    
    def download_adminotaur(self):
        """Download Adminotaur agent using workers.yaml registry"""
        print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Downloading agent registry...")
        
        # Download workers.yaml first
        if not self.download_workers_registry():
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Could not download workers registry")
            return
        
        # Parse workers.yaml to get adminotaur config
        try:
            registry_data = yaml.safe_load(self.workers_registry_path.read_text())
            adminotaur_config = registry_data.get("agents", {}).get("adminotaur", {})
            repo_url = adminotaur_config.get("repo_url", "")
            folder_path = adminotaur_config.get("folder_path", "")
            executable = adminotaur_config.get("executable", "")
            release_url = adminotaur_config.get("release_url", "")
            
            if not repo_url or not folder_path or not executable:
                print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Invalid registry format")
                return
            
            print(f"{Colors.BLUE}[SYSTEM]{Colors.RESET} Downloading Adminotaur agent...")
            
            # Use release_url if available, otherwise fall back to raw GitHub URL
            if release_url:
                agent_url = release_url
            else:
                raw_base = repo_url.replace("github.com", "raw.githubusercontent.com") + "/main/" + folder_path
                agent_url = raw_base + executable
            with urllib.request.urlopen(agent_url) as response:
                agent_data = response.read()
                self.adminotaur_agent_path.write_bytes(agent_data)
                self.adminotaur_agent_path.chmod(0o755)
                print(f"{Colors.GREEN}[✓]{Colors.RESET} Downloaded: {executable}")
                
        except Exception as e:
            print(f"{Colors.BLUE}[WARNING]{Colors.RESET} Failed to download Adminotaur: {e}")
    
    def decrypt_credential(self, credential_name):
        """Decrypt credential using Fernet (AES-128)"""
        if self._fernet is None:
            raise Exception("Not authenticated — cannot decrypt credential")
        cred_file = self.creds_dir / f"{credential_name}.enc"
        if not cred_file.exists():
            raise Exception(f"Credential file not found: {cred_file}")
        encrypted_bytes = cred_file.read_bytes()
        return self._fernet.decrypt(encrypted_bytes).decode()


def main():
    cli = DecyphertekCLI()
    cli.run()


if __name__ == "__main__":
    main()
