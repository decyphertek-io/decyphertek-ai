#!/usr/bin/env python3
import sys
import argparse


class DecyphertekCLI:
    def __init__(self):
        self.version = "0.1.0"
        
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
        
        if args.command:
            self.execute_command(args.command)
        else:
            self.interactive_mode()
    
    def execute_command(self, command):
        print(f"Executing: {command}")
        
    def interactive_mode(self):
        print("Decyphertek AI - Interactive Mode")
        print("Type 'exit' or 'quit' to exit\n")
        
        while True:
            try:
                user_input = input("decyphertek-ai> ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                    
                if not user_input:
                    continue
                    
                self.process_input(user_input)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                break
    
    def process_input(self, user_input):
        print(f"Processing: {user_input}")


def main():
    cli = DecyphertekCLI()
    cli.run()


if __name__ == "__main__":
    main()
