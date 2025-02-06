google_questions_schema = {
    "type": "array",
    "items": {
        "type": "string"
    }
}

token_clear_ques_prompt = """You are an expert in cryptocurrency analysis specializing in understanding meme coins. Based on the input data, generate a list of well-structured questions to search on Google that will help gather more context about the token, its purpose, and its meme. The questions should aim to clarify whether the token is part of a trending topic, its relevance to current events, the meaning behind the meme, and any important details about the project.

**Input:**
- **Token Website Content:** {token_website_content}
- **Tweeter content**: 
{tweeter_content}

**Output:** 
A list of questions to search on Google for further information. Ensure the questions are specific, relevant, and comprehensive.

Example:
1. What is the meaning of the meme associated with {token_name}?
2. Is {token_name} linked to any current trends or pop culture events?
3. What does {token_name}'s community say about its purpose or significance?
4. Are there any news articles or blogs discussing {token_name} and its potential?
5. Who is behind {token_name}, and what is their roadmap?

Now generate the questions:
"""