import vertexai.generative_models as generative_models
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
from typing import Optional

def create_model(model_name: str = "gemini-2.0-pro-exp-02-05") -> GenerativeModel:
    """
    Returns a GenerativeModel instance for chat generation.
    Adjust model name as needed.
    """
    return GenerativeModel(model_name)

def get_safety_settings():
    """
    Return a dictionary of your desired safety settings.
    """
    return {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH:
            generative_models.HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:
            generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:
            generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT:
            generative_models.HarmBlockThreshold.BLOCK_NONE,
    }

def multiturn_generate_content(model: GenerativeModel, prompt: str, schema: dict) -> Optional[str]:
    """
    Use Vertex AI Chat to generate structured (JSON) responses 
    according to the given content (prompt) and schema.
    """
    chat = model.start_chat(response_validation=False)
    safety_settings = get_safety_settings()
    try:
        response = chat.send_message(
            prompt,
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                response_schema=schema,
                max_output_tokens=8192,
                temperature=1,
                top_p=0.1,
            ),
            safety_settings=safety_settings
        )
        return response.candidates[0].content.parts[0]._raw_part.text
    except Exception as e:
        print(f"[ERROR multiturn_generate_content]: {e}")
        return None

def chat_generate_content(model: GenerativeModel, prompt: str) -> Optional[str]:
    """
    Use Vertex AI Chat model for non-schema text generation (plain text).
    """
    chat = model.start_chat(response_validation=False)
    safety_settings = get_safety_settings()
    generation_config = GenerationConfig(
        max_output_tokens=8192,
        temperature=1,
        top_p=0.1,
    )
    try:
        response = chat.send_message(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        return response.candidates[0].content.parts[0]._raw_part.text
    except Exception as e:
        print(f"[ERROR chat_generate_content]: {e}")
        return None
