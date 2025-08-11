def get_agent_model(config, agent_name):
    try:
        return config.get_config("agents")[agent_name]["model"]
    except Exception:
        if agent_name in ["management", "research", "architecture", "critic"]:
            return "o3"
        return "gpt-4.1-mini"


def get_agent_tokens(config, agent_name):
    # Reference: docs1/Token_Budget_Analysis.md, docs1/Technical_Specifications.md
    try:
        tokens = config.get_config("agents")[agent_name].get("max_tokens", 4096)
        if tokens < 1024:
            raise ValueError(
                f"Token allocation for {agent_name} is too low (got {tokens}). See Token_Budget_Analysis.md."
            )
        return tokens
    except Exception:
        return 4096


def is_reasoning_model(model_name):
    """Check if a model is a reasoning model that requires max_completion_tokens"""
    reasoning_models = ["o1", "o3", "o4"]
    return any(model_name.startswith(prefix) for prefix in reasoning_models)


def get_token_parameter_name(model_name):
    """Get the correct token parameter name based on model type"""
    if is_reasoning_model(model_name):
        return "max_completion_tokens"
    else:
        return "max_tokens"


def create_chat_completion_params(model, messages, max_tokens, **kwargs):
    """Create OpenAI chat completion parameters with correct token parameter name"""
    params = {
        "model": model,
        "messages": messages,
        **kwargs,  # Include any additional parameters like response_format, temperature, etc.
    }

    # Dynamically set the correct token parameter based on model type
    token_param = get_token_parameter_name(model)
    params[token_param] = max_tokens

    return params


def make_openai_request(client, model, messages, max_tokens, **kwargs):
    """Make an OpenAI chat completion request with automatic parameter handling"""
    params = create_chat_completion_params(model, messages, max_tokens, **kwargs)
    return client.chat.completions.create(**params)
