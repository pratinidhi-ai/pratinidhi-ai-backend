# sat_blueprint.py
SAT_BLUEPRINT = {
    "exam": "SAT",
    "rw": {
        "module1_balanced": {
            "total": 27,
            "topics": [
                "reading-and-writing|information-and-ideas",
                "reading-and-writing|craft-and-structure",
                "reading-and-writing|expression-of-ideas",
                "reading-and-writing|standard-english-conventions",
            ],
            "topic_mix": {
                "reading-and-writing|craft-and-structure": 0.28,
                "reading-and-writing|information-and-ideas": 0.26,
                "reading-and-writing|expression-of-ideas": 0.20,
                "reading-and-writing|standard-english-conventions": 0.26,
            },
            "difficulty_mix": {1: 0.20, 2: 0.25, 3: 0.35, 4: 0.15, 5: 0.05},
        },
        "module2_easy": {
            "total": 27,
            "topics": [
                "reading-and-writing|information-and-ideas",
                "reading-and-writing|craft-and-structure",
                "reading-and-writing|expression-of-ideas",
                "reading-and-writing|standard-english-conventions",
            ],
            "topic_mix": {
                "reading-and-writing|craft-and-structure": 0.28,
                "reading-and-writing|information-and-ideas": 0.26,
                "reading-and-writing|expression-of-ideas": 0.20,
                "reading-and-writing|standard-english-conventions": 0.26,
            },
            "difficulty_mix": {1: 0.40, 2: 0.25, 3: 0.25, 4: 0.08, 5: 0.02},
        },
        "module2_hard": {
            "total": 27,
            "topics": [
                "reading-and-writing|information-and-ideas",
                "reading-and-writing|craft-and-structure",
                "reading-and-writing|expression-of-ideas",
                "reading-and-writing|standard-english-conventions",
            ],
            "topic_mix": {
                "reading-and-writing|craft-and-structure": 0.28,
                "reading-and-writing|information-and-ideas": 0.26,
                "reading-and-writing|expression-of-ideas": 0.20,
                "reading-and-writing|standard-english-conventions": 0.26,
            },
            "difficulty_mix": {1: 0.10, 2: 0.25, 3: 0.35, 4: 0.20, 5: 0.10},
        },
    },
    "math": {
        "module1_balanced": {
            "total": 22,
            "topics": [
                "math|algebra",
                "math|advanced-math",
                "math|problem-solving-and-data-analysis",
                "math|geometry-and-trigonometry",
            ],
            "topic_mix": {
                "math|algebra": 0.35,
                "math|advanced-math": 0.35,
                "math|problem-solving-and-data-analysis": 0.15,
                "math|geometry-and-trigonometry": 0.15,
            },
            "difficulty_mix": {1: 0.20, 2: 0.20, 3: 0.30, 4: 0.10, 5: 0.10},
        },
        "module2_easy": {
            "total": 22,
            "topics": [
                "math|algebra",
                "math|advanced-math",
                "math|problem-solving-and-data-analysis",
                "math|geometry-and-trigonometry",
            ],
            "topic_mix": {
                "math|algebra": 0.35,
                "math|advanced-math": 0.35,
                "math|problem-solving-and-data-analysis": 0.15,
                "math|geometry-and-trigonometry": 0.15,
            },
            "difficulty_mix": {1: 0.27, 2: 0.23, 3: 0.23, 4: 0.14, 5: 0.13},
        },
        "module2_hard": {
            "total": 22,
            "topics": [
                "math|algebra",
                "math|advanced-math",
                "math|problem-solving-and-data-analysis",
                "math|geometry-and-trigonometry",
            ],
            "topic_mix": {
                "math|algebra": 0.35,
                "math|advanced-math": 0.35,
                "math|problem-solving-and-data-analysis": 0.15,
                "math|geometry-and-trigonometry": 0.15,
            },
            "difficulty_mix": {1: 0.09, 2: 0.09, 3: 0.05, 4: 0.41, 5: 0.36},
        },
    },
}
