# Semantic Workbench: Building custom Assistant with LangGraph framework

[Semantic Workbench](https://github.com/microsoft/semanticworkbench) is an open-source platform developed by Microsoft, designed to simplify the prototyping and development of intelligent assistants. It consists of a _backend service_, a _frontend user interface_ (UI) and multiple _assistant services_. The platform is highly adaptable and can support wide range of use cases from research to business applications and collaborative development.

This GitHub repo provides a step-by-step guide on building and deploying a LangGraph-based assistant within the Semantic Workbench environment. It includes code samples, explanations of some key concepts and demonstrates a specific use case implementation, i.e searching for and analysing arXiv publications to assist with a research process.

> [!NOTE]
> This step-by-step guide assumes that you have cloned the source code of Semantic Workbench **_v1_** from its official repo (https://github.com/microsoft/semanticworkbench) and using it on a Windows 11 machine.

## Table of contents:
- [Step 1: Setup of Semantic Workbench's backend](https://github.com/LazaUK/SemanticWorkbench-Assistant-LangGraph#step-1-setup-of-semantic-workbenchs-backend)
- [Step 2: Setup of Semantic Workbench's frontend](https://github.com/LazaUK/SemanticWorkbench-Assistant-LangGraph#step-2-setup-of-semantic-workbenchs-frontend)
- [Step 3: Deployment of LangGraph arXiv assistant](https://github.com/LazaUK/SemanticWorkbench-Assistant-LangGraph#step-3-deployment-of-langgraph-arxiv-assistant)
- [Appendix A: LangGraph assistant's business logic](https://github.com/LazaUK/SemanticWorkbench-Assistant-LangGraph#appendix-a-langgraph-assistants-business-logic)
- [Appendix B: LangGraph assistant's working demo](https://github.com/LazaUK/SemanticWorkbench-Assistant-LangGraph#appendix-b-langgraph-assistants-working-demo)

## Step 1: Setup of Semantic Workbench's backend
1. Ensure that your Windows 11's _execution policies_ are set correctly to allow the installation of necessary tools.
``` PowerShell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
Get-ExecutionPolicy -List
```
2. Install _Scoop_. Scoop is a command-line installer for Windows, that simplifies the installation of software by handling dependencies and configurations.
``` PowerShell
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```
3. After installing Scoop, reset the _execution policies_ to their default state.
``` PowerShell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Undefined
Get-ExecutionPolicy -List
```
4. Use Scoop to install the necessary dependencies for the backend. This includes _Python_, _Poetry_ (a dependency management tool) and _Make_ (a build automation tool).
``` PowerShell
scoop bucket add versions
scoop install python311
scoop install poetry
scoop install make
```
5. Navigate to the backend directory (**_semantic-workbench/v1/services_**) and use _Make_ to install the backend services.
``` PowerShell
make
```
6. Activate the Python virtual environment to ensure that the correct dependencies are used.
``` PowerShell
.venv\Scripts\activate.bat
```
7. Start the backend service to make it operational.
``` PowerShell
start-semantic-workbench-service
```

## Step 2: Setup of Semantic Workbench's frontend
1. _Node.js_ is a JavaScript runtime used for building and running the frontend. Install **Node.js v20** using Scoop.
``` PowerShell
scoop install nodejs-lts
```
2. Navigate to the frontend directory (**_semantic-workbench/v1/app_**) and install the necessary dependencies using _npm_ (Node Package Manager).
``` PowerShell
npm install
```
3.	Start the frontend service to make it operational.
``` PowerShell
npm start
```

## Step 3: Deployment of LangGraph arXiv assistant
1. Copy content of provided _assistants_ folder to the root of folder of your Semantic Workbench installation.


## Appendix A: LangGraph assistant's business logic
1. LangGraph arXiv assistant consists of 3 nodes: "_supervisor_", "_web_searcher_" and "_arxiv_analyser_".
``` Python
workflow = StateGraph(AgentState)
workflow.add_node("web_searcher", web_node)
workflow.add_node("arxiv_analyser", arxiv_node)
workflow.add_node("supervisor", supervisor_agent)
```
2. **Supervisor** node receives user's request and coordinates its processing with other nodes.
``` Python
def supervisor_agent(state):
    supervisor_chain = (
        prompt | llm.with_structured_output(routeResponse)
    )
    return supervisor_chain.invoke(state)
...
workflow.add_edge(START, "supervisor")
```
> [!NOTE]
> **Supervisor node's system prompt**: "_You are a supervisor tasked with managing a conversation between the following workers: 'web_searcher', 'arxiv_analyser'. Given the following user request, respond with the worker to act next. Each worker will perform a task and respond with their results and status. When finished, respond with FINISH._"
3. **Web Searcher** node is equipped with a search tool, powered by Tavily. It will search Internet on the research topic shared by **Supervisor** and return references to their publications in arXiv.
``` Python
tavily_tool = TavilySearchResults(max_results=5)
...
web_agent = create_react_agent(
    llm,
    tools=[tavily_tool],
    state_modifier="<YOUR_SYSTEM_PROMPT>"
)
```
> [!NOTE]
> **Web Searcher node's system prompt**: "_You are a web search expert. You will search the web for the latest Arxiv references on the topic, and return only the Arxiv references codes._"
4. **arXiv Analyser** node is equipped with LangGraph' arXiv tool. It will use arXiv reference numbers shared by **Supervisor** to extract publication date, authors and research brief's details. 
``` Python
arxiv_tool = ArxivQueryRun()
...
arxiv_agent = create_react_agent(
    llm,
    tools=[arxiv_tool],
    state_modifier="<YOUR_SYSTEM_PROMPT>"
)
```
> [!NOTE]
> **arXiv Analyser node's system prompt**: "_You are a specialist Arxiv analyzer. You will summarise found Arxiv papers, to advise when and by whom they were published, and what they are about._"
5. Visual representation of LangGraph arXiv assistant's nodes and edges is shown on the graph image below.
![LangGraph_nodes](/images/LangGraph_visual.jpeg)

## Appendix B: LangGraph assistant's working demo
Demo video of LangGraph arXiv assistant's use in Semantic Workbench's UI can be found here: [LINK TO YOUTUBE VIDEO TO BE ADDED LATER]().
