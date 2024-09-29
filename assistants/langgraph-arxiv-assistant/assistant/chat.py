# Copyright (c) Microsoft. All rights reserved.

# LangGraph ArXiv Assistant
#
# This assistant helps you mine ideas from artifacts.

import logging
import re
from typing import Any

import deepmerge
import tiktoken
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    ConversationParticipant,
    File,
    MessageType,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from .agents.attachment_agent import AttachmentAgent
from .config import AssistantConfigModel, ui_schema
from .responsible_ai.azure_evaluator import AzureContentSafetyEvaluator
from .responsible_ai.openai_evaluator import (
    OpenAIContentSafetyEvaluator,
    OpenAIContentSafetyEvaluatorConfigModel,
)

# Importing required packages
from typing import Annotated, Literal, Sequence, TypedDict
from pydantic import BaseModel
from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI
import functools
import operator
import os

logger = logging.getLogger(__name__)

#
# region Setup
#

# the service id to be registered in the workbench to identify the assistant
service_id = "langgraph-arxiv-assistant.laziz"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "LangGraph ArXiv Assistant"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "LangGraph-based assistant to analyse ArXiv publications."

# Extracting environment variables
AOAI_API_BASE = os.getenv("AZURE_OPENAI_API_BASE")
AOAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AOAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AOAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_API_DEPLOY")

# Setting Tavily as a search tool
tavily_tool = TavilySearchResults(max_results=5)

# Setting ArXiv as research tool
arxiv_tool = ArxivQueryRun()

#
# create the configuration provider, using the extended configuration model
#
config_provider = BaseModelAssistantConfig(AssistantConfigModel(), ui_schema=ui_schema)


# define the content safety evaluator factory
async def content_evaluator_factory(context: ConversationContext) -> ContentSafetyEvaluator:
    config = await config_provider.get_typed(context.assistant)

    # return the content safety evaluator based on the service type
    match config.service_config.service_type:
        case "Azure OpenAI":
            return AzureContentSafetyEvaluator(config.service_config.azure_content_safety_config)
        case "OpenAI":
            return OpenAIContentSafetyEvaluator(
                OpenAIContentSafetyEvaluatorConfigModel(openai_api_key=config.service_config.openai_api_key)
            )


# create the AssistantApp instance
assistant = AssistantApp(
    assistant_service_id=service_id,
    assistant_service_name=service_name,
    assistant_service_description=service_description,
    config_provider=config_provider,
    content_interceptor=ContentSafety(content_evaluator_factory),
)

#
# create the FastAPI app instance
#
app = assistant.fastapi_app()


# endregion

#
# region custom functions and classes
#

# Helper function to set agent node
def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["messages"][-1].content, name=name)]}

# Defining agent stats class
class AgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str

# endregion


#
# region Event Handlers
#
# The AssistantApp class provides a set of decorators for adding event handlers to respond to conversation
# events. In VS Code, typing "@assistant." (or the name of your AssistantApp instance) will show available
# events and methods.
#
# See the semantic-workbench-assistant AssistantApp class for more information on available events and methods.
# Examples:
# - @assistant.events.conversation.on_created (event triggered when the assistant is added to a conversation)
# - @assistant.events.conversation.participant.on_created (event triggered when a participant is added)
# - @assistant.events.conversation.message.on_created (event triggered when a new message of any type is created)
# - @assistant.events.conversation.message.chat.on_created (event triggered when a new chat message is created)
#


@assistant.events.conversation.message.chat.on_created
async def on_message_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle the event triggered when a new chat message is created in the conversation.

    **Note**
    - This event handler is specific to chat messages.
    - To handle other message types, you can add additional event handlers for those message types.
      - @assistant.events.conversation.message.log.on_created
      - @assistant.events.conversation.message.command.on_created
      - ...additional message types
    - To handle all message types, you can use the root event handler for all message types:
      - @assistant.events.conversation.message.on_created
    """

    # ignore messages from this assistant
    if message.sender.participant_id == context.assistant.id:
        return

    # update the participant status to indicate the assistant is thinking
    await context.update_participant_me(UpdateParticipant(status="exploring ArXiv universe..."))
    try:
        # respond to the conversation message
        await respond_to_conversation(
            context,
            message=message,
            metadata={"debug": {"content_safety": event.data.get(assistant.content_interceptor.metadata_key, {})}},
        )
    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


# Handle the event triggered when the assistant is added to a conversation.
@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """

    # send a welcome message to the conversation
    assistant_config = await config_provider.get_typed(context.assistant)
    welcome_message = assistant_config.welcome_message
    await context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


# endregion


#
# region Custom
#

# demonstrates how to respond to a conversation message echoing back the input message
async def respond_to_conversation(
    context: ConversationContext, message: ConversationMessage, metadata: dict[str, Any] = {}
) -> None:
    """
    Respond to a conversation message.
    """

    # Defining supervisor agent
    members = ["web_searcher", "arxiv_analyser"]
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        " following workers:  {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )
    # Our team supervisor is an LLM node. It just picks the next agent to process
    # and decides when the work is completed
    options = ["FINISH"] + members

    class routeResponse(BaseModel):
        next: Literal[*options]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), members=", ".join(members))

    llm = AzureChatOpenAI(
        api_key = AOAI_API_KEY,
        api_version = AOAI_API_VERSION,
        azure_endpoint = AOAI_API_BASE,
        azure_deployment = AOAI_DEPLOYMENT,
    )

    def supervisor_agent(state):
        supervisor_chain = (
            prompt | llm.with_structured_output(routeResponse)
        )
        return supervisor_chain.invoke(state)

    web_agent = create_react_agent(
        llm,
        tools=[tavily_tool],
        state_modifier="You are a web search expert. You will search the web for the latest Arxiv references on the topic, and return only the Arxiv references codes")
    web_node = functools.partial(
        agent_node,
        agent=web_agent,
        name="web_searcher"
    )

    arxiv_agent = create_react_agent(
        llm,
        tools=[arxiv_tool],
        state_modifier="You are a specialist Arxiv analyzer. You will summarise found Arxiv papers, to advise when and by whom they were published, and what they are about."
    )
    arxiv_node = functools.partial(
        agent_node,
        agent=arxiv_agent,
        name="arxiv_analyser"
    )

    workflow = StateGraph(AgentState)
    workflow.add_node("web_searcher", web_node)
    workflow.add_node("arxiv_analyser", arxiv_node)
    workflow.add_node("supervisor", supervisor_agent)

    # Defining edges
    for member in members:
        # We want our workers to ALWAYS "report back" to the supervisor when done
        workflow.add_edge(member, "supervisor")

    # The supervisor populates the "next" field in the graph state
    # which routes to a node or finishes
    conditional_map = {k: k for k in members}
    conditional_map["FINISH"] = END

    workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
    # Finally, add entrypoint
    workflow.add_edge(START, "supervisor")

    graph = workflow.compile()

    response = graph.invoke(
        {
            "messages": [
                HumanMessage(content=message.content)
            ]
        }
    )

    # send a new message with the echo response
    await context.send_messages(
        NewConversationMessage(
            content=response["messages"][-1].content,
            message_type=MessageType.chat,
            metadata={"generated_content": True}
        )
    )


# endregion
