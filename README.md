# Semantic Workbench: Building custom Assistant with LangGraph framework

[Semantic Workbench](https://github.com/microsoft/semanticworkbench) is an open-source platform developed by Microsoft, designed to simplify the prototyping and development of intelligent assistants. It consists of a _backend service_, a _frontend user interface_ (UI) and multiple _assistant services_. The platform is highly adaptable and can support wide range of use cases from research to business applications and collaborative development.

This GitHub repo provides a step-by-step guide on building and deploying a LangGraph-based assistant within the Semantic Workbench environment. It includes code examples and explanations of some key concepts. LangGraph-based assistant example demonstrates a specific use case: searching for and analysing arXiv publications to support the research process.

> Note: This step-by-step guide assumes that you have cloned the source code of Semantic Workbench from its official repo (https://github.com/microsoft/semanticworkbench) and using it on a Windows 11 machine.

## Table of contents:
- [Step 1: Setup of Semantic Workbench's backend](https://github.com/LazaUK/SemanticWorkbench-Assistant-LangGraph#step-1-setup-of-semantic-workbenchs-backend)
- [Step 2: Setup of Semantic Workbench's frontend](https://github.com/LazaUK/SemanticWorkbench-Assistant-LangGraph#step-2-setup-of-semantic-workbenchs-frontend)
- [Step 3: Deployment of LangGraph arXiv assistant]()

## Step 1: Setup of Semantic Workbench's backend
1. Ensure that your Windows 11's _execution policies_ are set correctly to allow the installation of necessary tools.
``` Shell
Get-ExecutionPolicy -List
```
2. Install _Scoop_. Scoop is a command-line installer for Windows, that simplifies the installation of software by handling dependencies and configurations.
``` Shell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```
3. After installing Scoop, reset the _execution policies_ to their default state.
``` Shell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Undefined
```
4. Use Scoop to install the necessary dependencies for the backend. This includes _Python_, _Poetry_ (a dependency management tool) and _Make_ (a build automation tool).
``` Shell
scoop bucket add versions
scoop install python311
scoop install poetry
scoop install make
```
5. Navigate to the backend directory (**semantic-workbench/v1/services**) and use _Make_ to install the backend services.
``` Shell
make
```
6. Activate the Python virtual environment to ensure that the correct dependencies are used.
``` Shell
.venv\Scripts\activate.bat
```
8. Start the backend service to make it operational.
``` Shell
start-semantic-workbench-service
```

## Step 2: Setup of Semantic Workbench's frontend
1. _Node.js_ is a JavaScript runtime used for building and running the frontend. Install **Node.js v20** using Scoop.
``` Shell
scoop install nodejs-lts
```
2. Navigate to the frontend directory (**semantic-workbench/v1/app**) and install the necessary dependencies using _npm_ (Node Package Manager).
``` Shell
npm install
```
9.	Start the frontend service to make it operational.
``` Shell
npm start
```

## Step 3: Deployment of LangGraph arXiv assistant
