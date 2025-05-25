import os
import pdb
import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

load_dotenv()
sys.path.append(".")


@dataclass
class LLMConfig:
    provider: str
    model_name: str
    temperature: float = 0.8
    base_url: str = None
    api_key: str = None


def create_message_content(text, image_path=None):
    """
    Creates a message content list containing text and optionally an image.
    
    If an image path is provided, the image is base64-encoded and appended to the content as an image URL dictionary. The image format is determined by the file extension.
     
    Args:
        text: The text content to include in the message.
        image_path: Optional path to an image file to include.
    
    Returns:
        A list of dictionaries representing the message content, including text and optionally an image.
    """
    content = [{"type": "text", "text": text}]
    image_format = "png" if image_path and image_path.endswith(".png") else "jpeg"
    if image_path:
        from src.utils import utils

        image_data = utils.encode_image(image_path)
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/{image_format};base64,{image_data}"},
            }
        )
    return content


def get_env_value(key, provider):
    """
    Retrieves the environment variable value for a given key and provider.
    
    Returns an empty string if the provider or key is not mapped or the environment variable is unset.
    """
    env_mappings = {
        "openai": {"api_key": "OPENAI_API_KEY", "base_url": "OPENAI_ENDPOINT"},
        "azure_openai": {
            "api_key": "AZURE_OPENAI_API_KEY",
            "base_url": "AZURE_OPENAI_ENDPOINT",
        },
        "google": {"api_key": "GOOGLE_API_KEY"},
        "deepseek": {"api_key": "DEEPSEEK_API_KEY", "base_url": "DEEPSEEK_ENDPOINT"},
        "mistral": {"api_key": "MISTRAL_API_KEY", "base_url": "MISTRAL_ENDPOINT"},
        "alibaba": {"api_key": "ALIBABA_API_KEY", "base_url": "ALIBABA_ENDPOINT"},
        "moonshot": {"api_key": "MOONSHOT_API_KEY", "base_url": "MOONSHOT_ENDPOINT"},
        "ibm": {"api_key": "IBM_API_KEY", "base_url": "IBM_ENDPOINT"},
    }

    if provider in env_mappings and key in env_mappings[provider]:
        return os.getenv(env_mappings[provider][key], "")
    return ""


def test_llm(config, query, image_path=None, system_message=None):
    """
    Invokes an LLM model with the specified configuration and query, optionally including an image and system message.
    
    Handles special cases for Ollama-based models, including DeepSeekR1, and prints the AI's response content. For other providers, constructs appropriate message objects and invokes the model, printing any reasoning content if available.
    """
    from src.utils import llm_provider

    # Special handling for Ollama-based models
    if config.provider == "ollama":
        if "deepseek-r1" in config.model_name:
            from src.utils.llm_provider import DeepSeekR1ChatOllama

            llm = DeepSeekR1ChatOllama(model=config.model_name)
        else:
            llm = ChatOllama(model=config.model_name)

        ai_msg = llm.invoke(query)
        print(ai_msg.content)
        if "deepseek-r1" in config.model_name:
            pdb.set_trace()
        return

    # For other providers, use the standard configuration
    llm = llm_provider.get_llm_model(
        provider=config.provider,
        model_name=config.model_name,
        temperature=config.temperature,
        base_url=config.base_url or get_env_value("base_url", config.provider),
        api_key=config.api_key or get_env_value("api_key", config.provider),
    )

    # Prepare messages for non-Ollama models
    messages = []
    if system_message:
        messages.append(SystemMessage(content=create_message_content(system_message)))
    messages.append(HumanMessage(content=create_message_content(query, image_path)))
    ai_msg = llm.invoke(messages)

    # Handle different response types
    if hasattr(ai_msg, "reasoning_content"):
        print(ai_msg.reasoning_content)
    print(ai_msg.content)


def test_openai_model():
    """
    Tests the OpenAI GPT-4o model by requesting a description of a sample image.
    """
    config = LLMConfig(provider="openai", model_name="gpt-4o")
    test_llm(config, "Describe this image", "assets/examples/test.png")


def test_google_model():
    # Enable your API key first if you haven't: https://ai.google.dev/palm_docs/oauth_quickstart
    config = LLMConfig(provider="google", model_name="gemini-2.0-flash-exp")
    test_llm(config, "Describe this image", "assets/examples/test.png")


def test_azure_openai_model():
    config = LLMConfig(provider="azure_openai", model_name="gpt-4o")
    test_llm(config, "Describe this image", "assets/examples/test.png")


def test_deepseek_model():
    config = LLMConfig(provider="deepseek", model_name="deepseek-chat")
    test_llm(config, "Who are you?")


def test_deepseek_r1_model():
    """
    Tests the DeepSeek Reasoner model by querying a numeric comparison with a system message.
    
    Invokes the DeepSeek Reasoner LLM to determine which of two numbers is greater, providing a system prompt to guide the AI's behavior.
    """
    config = LLMConfig(provider="deepseek", model_name="deepseek-reasoner")
    test_llm(
        config,
        "Which is greater, 9.11 or 9.8?",
        system_message="You are a helpful AI assistant.",
    )


def test_ollama_model():
    """
    Tests the Ollama Qwen2.5:7b model by requesting it to generate a ballad about LangChain.
    """
    config = LLMConfig(provider="ollama", model_name="qwen2.5:7b")
    test_llm(config, "Sing a ballad of LangChain.")


def test_deepseek_r1_ollama_model():
    config = LLMConfig(provider="ollama", model_name="deepseek-r1:14b")
    test_llm(config, "How many 'r's are in the word 'strawberry'?")


def test_mistral_model():
    config = LLMConfig(provider="mistral", model_name="pixtral-large-latest")
    test_llm(config, "Describe this image", "assets/examples/test.png")


def test_moonshot_model():
    config = LLMConfig(provider="moonshot", model_name="moonshot-v1-32k-vision-preview")
    test_llm(config, "Describe this image", "assets/examples/test.png")


def test_ibm_model():
    """
    Tests the IBM Meta-Llama 17B instruct model with an image description prompt.
    
    Sends a sample image and prompt to the IBM LLM provider and prints the AI's response.
    """
    config = LLMConfig(
        provider="ibm", model_name="meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
    )
    test_llm(config, "Describe this image", "assets/examples/test.png")


def test_qwen_model():
    config = LLMConfig(provider="alibaba", model_name="qwen-vl-max")
    test_llm(config, "How many 'r's are in the word 'strawberry'?")


if __name__ == "__main__":
    # test_openai_model()
    # test_google_model()
    test_azure_openai_model()
    # test_deepseek_model()
    # test_ollama_model()
    # test_deepseek_r1_model()
    # test_deepseek_r1_ollama_model()
    # test_mistral_model()
    # test_ibm_model()
    # test_qwen_model()
