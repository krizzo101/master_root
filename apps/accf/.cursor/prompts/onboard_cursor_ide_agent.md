<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Onboarding Prompt: Cursor IDE Agent for OAMAT","description":"Instructions and goals for onboarding the Cursor IDE Agent to autonomously assist with development, documentation, and orchestration tasks within the OAMAT project.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to understand the onboarding process for the Cursor IDE Agent in the OAMAT project. Focus on the instructions for exploring the codebase, documentation, and resources, and the stated goal of autonomous assistance. Use the sections and key elements to guide navigation and comprehension of the onboarding steps and objectives.","sections":[{"name":"Introduction and Overview","description":"Introduces the Cursor IDE Agent and outlines its primary task to onboard as an autonomous assistant for the OAMAT project within the IDE chat interface.","line_start":7,"line_end":12},{"name":"Onboarding Instructions","description":"Detailed step-by-step instructions guiding the agent through reviewing the project directory, reading documentation, analyzing the codebase, identifying resources, and preparing to assist.","line_start":13,"line_end":39},{"name":"Goal Statement","description":"Defines the ultimate goal for the agent to be fully prepared to autonomously assist with any assigned tasks in the OAMAT project via the Cursor IDE chat interface.","line_start":40,"line_end":46}],"key_elements":[{"name":"Onboarding Instructions List","description":"A numbered list detailing five key steps for the agent to follow during onboarding, including directory review, documentation reading, codebase analysis, resource identification, and preparation to assist.","line":14},{"name":"Project Directory Path","description":"Reference to the main project directory to explore: `src/applications/oamat/`, which is critical for understanding the project structure and components.","line":15},{"name":"Documentation Directory Path","description":"Reference to the documentation files located in `src/applications/oamat/docs/` which include architecture, agent docs, workflows, APIs, guides, and standards.","line":18},{"name":"Codebase Analysis Focus","description":"Emphasizes reviewing agent classes, workflow engine, and supporting modules to understand patterns for extension, workflow definition, and LLM integration.","line":23},{"name":"Additional Resources Identification","description":"Highlights the importance of locating configuration files, test cases, integration points, and recent changelog or roadmap updates.","line":27},{"name":"Agent Preparation Notes","description":"Instructions for the agent to be ready to answer questions, generate code/docs/tests, execute workflows, and stay updated with project standards.","line":31},{"name":"Goal Summary","description":"Concise statement of the agent's objective to be fully up to speed and ready to assist autonomously via the IDE chat interface.","line":40},{"name":"Completion Confirmation Note","description":"A closing remark prompting the agent to confirm readiness after completing onboarding and await the first task.","line":45}]}
-->
<!-- FILE_MAP_END -->

# Onboarding Prompt: Cursor IDE Agent for OAMAT

Welcome, Cursor IDE Agent!

Your first task is to onboard yourself as an autonomous agent capable of assisting with development, documentation, and orchestration tasks in the OAMAT project. You will operate in the chat interface of the IDE and may be tasked with work to support other agents and users.

## Onboarding Instructions

1. **Review the OAMAT Application Directory**
   - Explore all subdirectories under `src/applications/oamat/`.
   - Understand the project structure, agent modules, workflows, and utilities.

2. **Read the Documentation**
   - Carefully read all files in `src/applications/oamat/docs/`, including:
     - Architecture overview
     - Agent documentation
     - Workflow examples
     - API specifications
     - Developer, user, and deployment guides
     - Standards and ADRs

3. **Analyze the Codebase**
   - Review the implementation of all agent classes, workflow engine, and supporting modules.
   - Note patterns for agent extension, workflow definition, and LLM integration.

4. **Identify Additional Resources**
   - Look for configuration files, test cases, and integration points (API, DB, web UI, Airflow).
   - Check for any recent changes in the changelog or roadmap.

5. **Prepare to Assist**
   - Be ready to answer questions, generate code/docs/tests, and execute workflows as requested in the chat interface.
   - Stay up to date with project rules, standards, and best practices.

## Goal
Your goal is to be fully up to speed on the OAMAT project and ready to autonomously assist with any development, documentation, or orchestration task assigned via the Cursor IDE chat interface.

---

*Once you have completed onboarding, confirm your readiness and await your first task.*
