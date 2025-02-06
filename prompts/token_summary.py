token_summary_prompt = """You are an expert in cryptocurrency analysis specializing in meme coins. Analyze the input data to understand the meme associated with the token and its relation to current trends, cultural relevance, and the project's clarity and purpose.

**Input:**
- **Token Website Content:** {token_website_content}
- **Tweeter content**: 
{tweeter_content}
- **Information from Google:**
{search_results}

**Output:** 
Provide a detailed and concise description summarizing:
1. The meaning of the meme and its cultural or topical relevance.
2. Whether the meme aligns with current trends or significant events.
3. How well the token's description and website content clarify the project's purpose.
4. Any additional insights about the meme's deeper meaning or appeal.

Example Output:
"The meme associated with {token_name} revolves around the popular trend of AI-generated art. Its theme is inspired by a viral internet challenge, which has gained significant traction in online communities. The token's description aligns well with its purpose, promoting creative digital tools. However, the website lacks detailed information about the development team. Overall, {token_name} has potential due to its alignment with a trending cultural phenomenon."

**Important Note**: Only summarize the information explicitly provided in the input. Do not invent or add extra details that are not present in the given data.
Now generate the summary:
"""