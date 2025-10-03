import logging

from apps.agent.core.langfuse_connection import get_langfuse

logger = logging.getLogger(__name__)


def retrieve_prompt(prompt_name: str, variables: dict = None) -> str | None:
    """Retrieve and format a prompt template with given keyword arguments.

    Args:
        prompt_name (str): The name of the prompt to retrieve.
        variables (dict, optional): A dictionary of variables to replace in the prompt template. Defaults to {}.

    Returns:
        str | None: The formatted prompt string, or None if retrieval fails.
    """
    lf = get_langfuse().client
    if not lf:
        logger.warning("Langfuse client not initialized.")
        return None

    try:
        prompt_obj = lf.get_prompt(prompt_name)
        if not prompt_obj:
            logger.warning("Langfuse prompt not found: %s", prompt_name)
            return None

        compiled_text = prompt_obj.compile(**(variables or {}))
        return compiled_text
    except Exception as e:
        logger.warning("retrieve_prompt failed for %s: %s", prompt_name, e)
        return None
