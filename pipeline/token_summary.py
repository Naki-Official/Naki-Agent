import json

from vertex_ai.vertex_utils import multiturn_generate_content, chat_generate_content, create_model
from prompts.google_questions import google_questions_schema, token_clear_ques_prompt
from prompts.token_summary import token_summary_prompt
from utils.webcrawler import extract_text_from_url
from utils.search import search  # or replace with your own

model = create_model()


def get_token_summary(token_data: dict) -> str:
    """
    Step 3:
      1) Generate questions using 'token_clear_ques_prompt'
      2) Possibly do your web search with the questions
      3) Summarize the results into a 'token_summary'
    """
    # web_content = = extract_text_from_url(token_data.
    for website in token_data.get("info",{}).get("websites", []):
        if website.get("url", ""):
            web_content = extract_text_from_url(website.get("url", ""))

    name = token_data.get("baseToken",{}).get("name", "")
    x_content = token_data.get("x_content", "")

    final_prompt = token_clear_ques_prompt.format(
        tweeter_content = x_content,
        token_website_content=web_content,
        token_name=name
    )
    print(final_prompt)
    ques_json_str = multiturn_generate_content(model, final_prompt, google_questions_schema)
    if not ques_json_str:
        return "N/A"

    try:
        ques_list = json.loads(ques_json_str)
    except:
        ques_list = []

    # Build "search_results"
    search_results = ""
    for q in ques_list:
        answers = search(q)  
        search_results += f"**{q}**\n{answers}\n\n"

    summ_prompt = token_summary_prompt.format(
        tweeter_content = x_content,
        token_website_content=web_content,
        search_results=search_results,
        token_name=name
    )
    summary = chat_generate_content(model, summ_prompt)
    return summary
