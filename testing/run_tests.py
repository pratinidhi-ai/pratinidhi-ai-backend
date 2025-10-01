#!/usr/bin/env python3
"""
AI Tutor Testing Launcher

This script provides easy access to different testing tools for the AI tutor system.
"""

import sys
import os
import subprocess

def show_help():
    """Display help information."""
    print("🧪 AI TUTOR TESTING TOOLS")
    print("=" * 50)
    print("Usage: python run_tests.py [command]")
    print()
    print("Available commands:")
    print("  chat       - Launch interactive chat tester")
    print("  prompt     - Launch prompt testing tool")
    print("  help       - Show this help message")
    print()
    print("Examples:")
    print("  python run_tests.py chat     # Start chat with AI tutor")
    print("  python run_tests.py prompt   # Test prompt generation")
    print()
    print("If no command is provided, the chat tester will start.")

def launch_chat_tester():
    """Launch the interactive chat tester."""
    print("🚀 Launching AI Tutor Chat Tester...")
    try:
        # Import and run the chat tester
        from chat_tester import main as chat_main
        chat_main()
    except ImportError as e:
        print(f"❌ Error importing chat tester: {e}")
        print("Make sure all dependencies are installed.")
    except Exception as e:
        print(f"❌ Error running chat tester: {e}")

def launch_prompt_tester():
    """Launch the prompt tester."""
    print("🚀 Launching Prompt Tester...")
    try:
        # Import and run the prompt tester
        from prompt_tester import main as prompt_main
        prompt_main()
    except ImportError as e:
        print(f"❌ Error importing prompt tester: {e}")
        print("Make sure all dependencies are installed.")
    except Exception as e:
        print(f"❌ Error running prompt tester: {e}")

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ["help", "-h", "--help"]:
            show_help()
        elif command == "chat":
            launch_chat_tester()
        elif command == "prompt":
            launch_prompt_tester()
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python run_tests.py help' for available commands.")
    else:
        # Default to chat tester
        launch_chat_tester()

if __name__ == "__main__":
    main()