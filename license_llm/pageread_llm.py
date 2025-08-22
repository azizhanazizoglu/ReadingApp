
import os
import openai

def map_json_to_html_fields(html_string: str, ruhsat_json: dict, model="gpt-4o"):
    """
    Given an HTML form and a JSON object with data to fill, use the LLM to determine which JSON field should be filled into which input/select in the HTML, and which button(s) should be clicked. The LLM should analyze all clues (label, placeholder, id, name, type, etc.) and return a mapping as JSON.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = f"""
You are an advanced web form automation assistant. You will be given the HTML code of a web form (which may be part of a multi-page flow) and a JSON object containing the data to be filled in.

Instructions:
1. Analyze the HTML to determine which fields from the JSON are present on this page. Only map and fill the fields that exist on this page. Ignore fields that are not present in the HTML.
2. For each present field, match it to the most appropriate input or select element in the HTML. Use all available clues: label text, placeholder, id, name, type, etc.
3. Identify which button(s) should be clicked to submit or continue to the next page (e.g., 'Next', 'Continue', 'DEVAM').
4. If the page contains a title, heading, or other unique identifier, use it to help determine context, but do not include it in the output.
5. Return only the mapping in the following JSON format. Do not add any explanation or extra text:
{{
  "field_mapping": {{
    "json_field_name": "input#id or input[name=] or label text"
  }},
  "actions": ["click#button_id or button text"]
}}

Example mapping:
{{
  "field_mapping": {{
    "plaka_no": "input[name=plateNo]"
  }},
  "actions": ["click#Next"]
}}

Here is the HTML:
"""
    prompt += html_string[:8000]  # limit for token safety
    prompt += "\n\nData to fill (JSON):\n" + str(ruhsat_json)
    prompt += "\n\nReturn only the mapping JSON. Do not add any explanation."

    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=512
    )
    return response.choices[0].message.content.strip()