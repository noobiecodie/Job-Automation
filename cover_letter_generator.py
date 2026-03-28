"""
cover_letter_generator.py

Generates short, tailored cover letters using the OpenAI API.

Important for beginners:
- You must set your OpenAI API key as an environment variable named OPENAI_API_KEY.
- This module will fail gracefully (and return an empty string) if the API call fails.
"""

from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI


# This is the user's profile that we will personalize the letter with.
PROFILE = {
    "name": "Aarya Vaidya",
    "role": "UI/UX Designer",
    "experience": "Worked at Feelpixel on CARS24 insurance service project",
    "skills": "UX strategy, UI design systems, Figma, product thinking",
}


def _get_client() -> Optional[OpenAI]:
    """
    Create an OpenAI client if the API key is available.

    We intentionally keep this beginner-friendly:
    - Set OPENAI_API_KEY in your environment
    - The OpenAI library reads it automatically, but we still check and guide the user
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print(
            "[cover_letter] Missing OPENAI_API_KEY.\n"
            "  Set it first, then run again. See README.md for steps."
        )
        return None

    # OpenAI() automatically uses OPENAI_API_KEY from the environment.
    return OpenAI()


def generate_cover_letter(company: str, role: str, description: str, model: str = "gpt-4.1-mini") -> str:
    """
    Generate a concise, professional, tailored cover letter (150–200 words).

    Inputs:
    - company: company name
    - role: job title
    - description: job description text

    Output:
    - A plain-text cover letter string, or "" if generation fails.
    """
    client = _get_client()
    if client is None:
        return ""

    # Keep prompts clear and structured so results are consistent.
    system_message = (
        "You are an expert career coach and professional copywriter. "
        "Write concise, confident cover letters for UI/UX designers."
    )

    user_message = f"""
Write a professional cover letter that is:
- 150–200 words
- tailored to the job description
- confident and friendly (not overly casual)
- specific to the company and role

Candidate profile:
Name: {PROFILE['name']}
Target role: {PROFILE['role']}
Experience: {PROFILE['experience']}
Skills: {PROFILE['skills']}

Job to apply for:
Company: {company}
Role: {role}
Job description:
{description}

Rules:
- Do NOT use placeholders like [Hiring Manager]
- Do NOT invent specific achievements or numbers not provided
- End with a short call to action (interview / portfolio discussion)
""".strip()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            # Lower temperature = more consistent, professional tone.
            temperature=0.4,
        )

        text = (response.choices[0].message.content or "").strip()
        return text

    except Exception as exc:
        # Catch-all so the script doesn't crash for a non-developer.
        print(f"[cover_letter] OpenAI API error for {company} / {role}\n  Reason: {exc}")
        return ""

