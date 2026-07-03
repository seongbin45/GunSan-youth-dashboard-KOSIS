
Languages: [English](/seongbin45/GunSan-youth-dashboard-KOSIS/README.md) | [한국어](/seongbin45/GunSan-youth-dashboard-KOSIS/README.ko.md)

# FinFit

FinFit is a Streamlit MVP that helps young adults and first-time job seekers easily understand scattered financial and policy information and quickly find benefit candidates that match their conditions.

## 1. Why We Built It

Youth benefit information is fragmented across institutions, and eligibility conditions often include unfamiliar terms such as median income, non-homeownership, tax exemption, and matching support. Many users give up without even knowing what benefits are available to them.

FinFit addresses this problem from the following perspectives:

* Maintain the latest youth benefits in an updatable structure
* Provide personalized benefit recommendations
* Explain difficult financial information in simple language

## 2. What Problems It Solves

User feedback repeatedly highlighted three recurring needs:

* Automatic or up-to-date benefit information
* Personalized recommendations based on age, income, occupation, and housing status
* Consolidated view of financial and policy information scattered across multiple institutions

This update focuses on creating a maintainable MVP structure by reducing duplicate home screens, hard-coded policy conditions, and mixed routing, rather than adding new features.

## 3. Core Features

* **Personalized Benefit Recommendations**: Create a `UserProfile` and use `match_policies(profile, policies)` to recommend suitable policy candidates.
* **Policy Data Management**: Policy conditions are managed in `data/policies.json` instead of being hard-coded in the Python UI code.
* **Youth Benefit Updates**: Sync with the OnTong Youth API, check cache status, data freshness, and fallback behavior.
* **Easy Financial Explanations**: Explain policy and financial terms that are difficult for first-time job seekers in plain language.

## 4. System Architecture

app.py pages/ services/ models.py policy_loader.py recommendation.py data/ policies.json finfit_youth/ client.py cache_store.py service.py tests/ docs/
**Recommendation flow:**

User Input -> UserProfile -> load_policies() -> match_policies(profile, policies) -> Render recommendation results
**Operational status flow:**

OnTong Youth API -> YouthDataService -> CacheStore -> Last sync / Data freshness / API status / Fallback indicator
## 5. Demo

Demo GIFs will be added to the `assets/` directory later.

Target demo screens:

* Normal API connection screen
* Cache fallback screen after API failure
* Personalized benefit recommendation screen after entering conditions

## 6. Testing

pytest

Verification items:

* Policy JSON required field validation
* Conditional verification of recommendation logic
* API failure and cache fallback verification
* Existing YouthDataService cache/detail retrieval flow verification

Tests run on push/PR via GitHub Actions (`.github/workflows/test.yml`).

## 7. Tech Stack

* Python
* Streamlit
* Pandas
* Plotly
* SQLite
* Requests
* pytest

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
Some external API features require API keys in Streamlit secrets or environment variables.
Non-Goals
FinFit v1 does not provide:
	•	Financial product subscription agency
	•	Legal eligibility determination
	•	Investment advisory
	•	Alternative services to financial institutions
	•	Community, ranking, friend, or SNS features
	•	Flutter migration
	•	Database replacement
Policy recommendations are primary candidate suggestions to help verify official sources.

