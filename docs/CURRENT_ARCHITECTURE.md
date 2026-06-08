# Current Architecture

This document records the baseline before the MVP cleanup.

## Current Pages

- `app.py`: Main entrypoint, home content, savings guide fragments, feedback form, and navigation links were mixed together.
- `pages/0_Home.py`: Duplicate home page with similar navigation and feature cards.
- `pages/Main_Screen.py`: Duplicate main screen with budget UI and hardcoded policy matching.
- `pages/2_AI와_대화하기.py`: AI agent page with provider code and hardcoded benefit logic.
- `pages/3_정부 지원 혜택 목록.py`: Static benefit list plus duplicated update-page logic.
- `pages/4_군산시민 맞춤 혜택 찾기.py`: User input UI and policy matching logic mixed in one Streamlit page.
- `pages/7_청년혜택업데이트.py`: Public API list/search page backed by `finfit_youth`.

## Current Problems

- Home screen is duplicated across `app.py`, `pages/0_Home.py`, and `pages/Main_Screen.py`.
- Some pages call `st.set_page_config` more than once or after another Streamlit command.
- Page routing uses hardcoded filenames in several places.
- Policy eligibility logic is hardcoded in UI pages.
- Policy data cannot be updated without editing Python code.
- Tests exist for the youth API service, but recommendation and policy data validation tests are missing.

## Existing Strengths

- `finfit_youth` already separates API client, cache store, rate limiting, scheduler, and service logic.
- The app already focuses on the right MVP themes: youth benefits, personalized matching, and easy explanations.
- The repository already has a README, Streamlit configuration, and a GitHub Actions workflow for reboot automation.
