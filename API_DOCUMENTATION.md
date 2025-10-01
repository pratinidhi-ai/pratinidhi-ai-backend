# AI Tutor Backend - System Prompt Implementation

## Overview

This implementation provides a comprehensive AI tutor system with dynamic prompt generation based on user preferences, educational requirements, and tutor personalities.

## Key Features

### 1. Dynamic System Prompt Generation
- **Personality-based tutoring**: Choose from 8 different tutor personalities (Einstein, Dumbledore, Yoda, etc.)
- **Subject specialization**: Customize prompts based on specific subjects
- **Educational level adaptation**: Adjust content complexity for elementary to graduate levels
- **Exam preparation**: Focus on specific exams (SAT, GRE, AP, etc.)
- **Interest-based examples**: Use student interests to create relatable analogies
- **Goal-oriented learning**: Align teaching with student objectives

### 2. Lecture Notes Integration
- **Structured teaching**: Follow predefined lecture content
- **Content restrictions**: Ensure tutors stay within provided material
- **Progressive learning**: Point-by-point teaching with assessments
- **Comprehensive evaluation**: End-of-session quizzes and summaries

## API Usage

### Starting a Tutor Session

```http
POST /tutor/start-session
```

**Request Body:**
```json
{
  "user_id": "user123",
  "personality": "albert_einstein",
  "language": "english",
  "subject": "Physics",
  "level": "high_school", 
  "exam": "AP Physics",
  "interests": ["basketball", "video games", "music"],
  "goals": ["improve grades", "understand concepts better"],
  "lecture_notes": "Chapter 1: Introduction to Motion\\n- Position and displacement\\n- Velocity and acceleration"
}
```

**Response:**
```json
{
  "session_id": "uuid-generated-session-id",
  "system_prompt": "You are an AI tutor who is friendly, patient..."
}
```

### Sending Messages

```http
POST /tutor/{session_id}/message
```

**Request Body:**
```json
{
  "message": "Can you explain Newton's first law?"
}
```

**Response:**
```json
{
  "ai_response": "Ah, excellent question! Newton's first law...",
  "session_active": true,
  "message_count": 2
}
```

## Available Personalities

### 1. Albert Einstein (`albert_einstein`)
- Uses thought experiments and analogies
- Emphasizes curiosity and questioning
- Gentle, encouraging approach

### 2. Professor Dumbledore (`professor_dumbledore`)
- Wise, patient guidance
- Uses stories and metaphors
- Believes in student potential

### 3. Yoda (`yoda`)
- Inverted sentence structure
- Emphasizes patience and practice
- Uses Force/nature metaphors

### 4. Sherlock Holmes (`sherlock_holmes`)
- Logical deduction approach
- Attention to detail
- Methodical problem-solving

### 5. Elon Musk (`elon_musk`)
- First principles thinking
- Practical applications
- Bold, innovative approach

### 6. Wednesday Addams (`wednesday_addams`)
- Dark humor and sarcasm
- Intelligent, perceptive insights
- Doesn't sugarcoat concepts

### 7. Steve Jobs (`steve_jobs`)
- Simplicity and elegance
- Design thinking approach
- "Think different" philosophy

### 8. Marie Curie (`marie_curie`)
- Persistence and dedication
- Scientific method emphasis
- Inspiring and empowering

## Educational Levels

- `elementary`: Simple language, basic concepts
- `middle_school`: Clear explanations with some complexity
- `high_school`: Advanced concepts and terminology
- `college`: Sophisticated ideas and reasoning
- `graduate`: Advanced theories and research concepts
- `professional`: Practical applications and industry knowledge

## Lecture Notes Features

When lecture notes are provided:

1. **Content Restriction**: Tutors only use provided material
2. **Structured Teaching Plan**:
   - Point-by-point explanation
   - Understanding checks after each point
   - Quick assessments (1-2 questions per point)
   - Overall Q&A session
   - 5-question comprehensive quiz
   - Detailed explanations for quiz answers
   - Session summary and feedback

## Code Structure

### Files Modified/Created:

1. **`models/tutor_session_schema.py`**
   - Added new fields for session customization
   - Enhanced `to_dict()` method

2. **`config/personalities.json`**
   - Personality definitions with traits and catchphrases

3. **`helper/prompt_builder.py`**
   - Main prompt building logic
   - Modular section builders
   - Personality integration

4. **`routes/tutor_routing.py`**
   - Updated session creation endpoint
   - Enhanced message handling
   - Better error handling

5. **`helper/ai_api.py`**
   - Updated to use session system prompts
   - Added safety guardrails

6. **`testing/`** (New directory)
   - Comprehensive test suite
   - Unit tests for all components

## Usage Examples

### Basic Session
```python
# Simple math tutor with Einstein personality
{
  "user_id": "student123",
  "personality": "albert_einstein", 
  "subject": "Mathematics",
  "level": "high_school"
}
```

### Advanced Session with Lecture Notes
```python
# Chemistry tutor with structured content
{
  "user_id": "student123",
  "personality": "marie_curie",
  "subject": "Chemistry", 
  "level": "college",
  "exam": "MCAT",
  "interests": ["research", "lab work"],
  "goals": ["med school admission"],
  "lecture_notes": "Chapter 5: Chemical Bonding\\n- Ionic bonds\\n- Covalent bonds\\n- Metallic bonds"
}
```

## Testing

Run the test suite:
```bash
cd testing
python run_tests.py
```

Run specific tests:
```bash
python run_tests.py prompt    # Test prompt builder
python run_tests.py session   # Test session functionality
```

## Error Handling

The system includes comprehensive error handling for:
- Invalid personality selections (falls back to professional style)
- Missing required fields (returns 400 with error message)
- Session not found (returns 404)
- API failures (returns 500 with details)

## Security Features

- Input validation for all parameters
- Safety guardrails in system prompts
- Content filtering for inappropriate requests
- Session isolation and cleanup