from vertex_ai.vertex_utils import chat_generate_content, create_model
from prompts.tweet_generation import tweet_generation_prompt

model = create_model()


def generate_tweet(token_data: dict, cookieData: dict, analysis_result: dict, recommendation: str) -> str:
    prompt = tweet_generation_prompt.format(
        tokenName=token_data.get("baseToken",{}).get("name", ""),
        price=token_data.get("price", ""),
        token_summary=token_data.get("token_summary", ""),
        mindshare=token_data.get("mindshare", ""),
        mindshareDeltaPercent=token_data.get("mindshareDeltaPercent", ""),
        mindshare_ratio = token_data.get("mindshare_ratio", ""),
        avg_mindshare_ratio = token_data.get("avg_mindshare_ratio", ""),
        technicalAnalysis=analysis_result,
        cookieData=cookieData,
        recommendation=recommendation
    )
    return chat_generate_content(model, prompt)