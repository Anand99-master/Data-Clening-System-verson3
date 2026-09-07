"""
modules/ai_recommendations.py — Phase 4: Advanced AI Feature (Module 23)

The AI's ONLY job is to look at the profiling summary and suggest which
of the tool's existing deterministic cleaning steps to run and on which
columns. It never touches the data directly and never invents cleaning
logic of its own — actual cleaning always goes through the same
pandas-based modules used elsewhere in the app. This mirrors the doc:

    "AI recommendation dega, lekin actual cleaning deterministic Python
     rules se hogi. Ye safer architecture hai."

Requires an Anthropic API key (passed in, or read from ANTHROPIC_API_KEY
env var). If the `anthropic` package or a key isn't available, callers
should treat this feature as optional and hide/disable it.
"""

import json
import os

RECOMMENDATION_SCHEMA_PROMPT = """You are helping review a tabular dataset's \
data-quality profile and recommend which cleaning actions to run.

You will be given a JSON profile: per-column type, missing count, missing %, \
unique count, plus overall row/column counts and duplicate row count.

Respond with ONLY a JSON array (no prose, no markdown fences) of recommendation \
objects, each with this exact shape:
{
  "issue": "short human-readable description of the problem",
  "column": "the column name this applies to, or null if dataset-wide (e.g. duplicates)",
  "action": "one of: remove_duplicates | fill_missing_mean | fill_missing_median | fill_missing_mode | trim_spaces | standardize_text | convert_type_integer | convert_type_float | standardize_dates | detect_outliers",
  "reason": "one short sentence on why"
}
Only recommend actions that plausibly apply given the profile data. Keep the \
list to at most 8 items, most important first."""


def _get_client(api_key: str = None):
    from anthropic import Anthropic
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("No Anthropic API key provided (pass one in, or set ANTHROPIC_API_KEY).")
    return Anthropic(api_key=key)


def get_recommendations(profile_summary: dict, api_key: str = None) -> list:
    """
    profile_summary: dict produced by building a small JSON-friendly summary
    of profiling.profile_dataframe() output plus dataset-level stats.
    Returns a list of recommendation dicts (see schema above).
    """
    client = _get_client(api_key)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=RECOMMENDATION_SCHEMA_PROMPT,
        messages=[{"role": "user", "content": json.dumps(profile_summary)}],
    )

    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    text = text.strip()
    # tolerate accidental markdown fences even though we asked for none
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[-1] if "\n" in text else text

    try:
        recommendations = json.loads(text)
    except json.JSONDecodeError:
        return []

    if not isinstance(recommendations, list):
        return []
    return recommendations


def build_profile_summary(df, profile_df) -> dict:
    """Turns profiling.profile_dataframe() output + df into the JSON payload sent to the AI."""
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "column_profile": profile_df.to_dict(orient="records"),
    }
