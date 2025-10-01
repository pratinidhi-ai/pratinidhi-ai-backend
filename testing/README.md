# Testing Tools for AI Tutor Backend

This directory contains interactive testing tools for the AI tutor system. Instead of traditional unit tests, these tools allow you to test the system in real-time and see immediate results.

## Available Tools

### 1. Chat Tester (`chat_tester.py`)

An interactive terminal chat interface that lets you:
- Create tutor sessions with different personalities
- Chat directly with the AI tutor
- Test different configurations (subject, level, interests, etc.)
- Add lecture notes and see structured teaching
- View system prompts in real-time

**Usage:**
```bash
python chat_tester.py
```

**Features:**
- Interactive session creation
- Real-time AI responses (requires OpenAI API key)
- Command system (`/help`, `/new`, `/prompt`, etc.)
- Support for all personality types
- Lecture notes testing

### 2. Prompt Tester (`prompt_tester.py`)

A tool for testing and validating system prompt generation without AI API calls:
- Test all personalities quickly
- Generate detailed prompts with various parameters
- Interactive prompt builder
- Compare how different personalities handle the same subject
- Save prompts to files for inspection

**Usage:**
```bash
python prompt_tester.py              # Interactive menu
python prompt_tester.py all          # Test all personalities
python prompt_tester.py albert_einstein  # Test specific personality
python prompt_tester.py compare Physics   # Compare personalities for Physics
```

### 3. Test Launcher (`run_tests.py`)

Simple launcher for the testing tools:

```bash
python run_tests.py          # Start chat tester (default)
python run_tests.py chat     # Start chat tester
python run_tests.py prompt   # Start prompt tester
python run_tests.py help     # Show help
```

## Quick Start

1. **Test Prompt Generation:**
   ```bash
   cd testing
   python prompt_tester.py
   ```

2. **Chat with AI Tutor:**
   ```bash
   cd testing
   python chat_tester.py
   ```
   Note: Requires OpenAI API key configured in your environment.

3. **Quick Personality Test:**
   ```bash
   python prompt_tester.py all
   ```

## Testing Scenarios

### Basic Personality Test
```bash
python prompt_tester.py albert_einstein
```
This will show how Einstein personality generates prompts with different parameters.

### Full Chat Session
```bash
python chat_tester.py
# Follow prompts to create session
# Try: /new -> select personality -> chat normally
```

### Lecture Notes Testing
1. Start chat tester: `python chat_tester.py`
2. Use `/new` command
3. When prompted for lecture notes, enter:
   ```
   Chapter 1: Newton's Laws
   - First Law: Objects at rest stay at rest
   - Second Law: F = ma
   - Third Law: Action-reaction pairs
   
   [Press Enter twice to finish]
   ```
4. Chat with the tutor and see how it follows the structured teaching plan

### Comparing Personalities
```bash
python prompt_tester.py compare Mathematics
```
This shows how different personalities (Einstein, Dumbledore, Yoda, etc.) would approach teaching Mathematics.

## Debugging Workflow

When making changes to prompts:

1. **Test Prompt Generation First:**
   ```bash
   python prompt_tester.py interactive
   ```
   Generate prompts with your changes and verify the output looks correct.

2. **Test with Chat Interface:**
   ```bash
   python chat_tester.py
   ```
   Create a session and have a real conversation to see how the changes affect AI responses.

3. **Test Edge Cases:**
   - Try different personalities
   - Test with and without lecture notes
   - Try different education levels
   - Test with various interests and goals

## Configuration

The tools automatically load:
- Personality configurations from `../config/personalities.json`
- System modules from the parent directory
- OpenAI API settings from environment variables (for chat tester)

## Tips

- Use the prompt tester to quickly validate changes without API calls
- Use the chat tester to see real AI behavior
- Save interesting prompts using the prompt tester's save feature
- Use `/prompt` command in chat tester to see the exact system prompt being used
- Try different combinations of parameters to test edge cases