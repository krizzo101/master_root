# Consult Agent Workflows and Procedures

## Mandatory Pre-Submission Thinking Ritual

### **🎯 Why This Ritual is Mandatory**

The consult agent knows **NOTHING** about your project, your work, or your context. Without proper context, you'll get generic, unhelpful responses. This ritual ensures you:

- **Stop and think systematically** about what you're asking
- **Identify all necessary context** the consult agent needs
- **Review your own work** for potential mistakes before asking for help
- **Package everything properly** so the consult agent can provide informed advice
- **Catch logical gaps** in your own thinking by explaining it to yourself

### **🧠 MANDATORY THINKING TOOL RITUAL**

**Before ANY consult agent call, you MUST use the thinking tool to answer these questions:**

```python
# MANDATORY PRE-SUBMISSION THINKING RITUAL
mcp_thinking_sequentialthinking({
    "thought": "I am about to make a consult agent call. Let me think through what I need to provide...",
    "nextThoughtNeeded": True,
    "thoughtNumber": 1,
    "totalThoughts": 5
})
```

#### **📋 MANDATORY CHECKLIST QUESTIONS**

**You MUST answer these specific, concrete questions using the thinking tool before proceeding:**

1. **🎯 REQUEST CLARITY**
   - What exactly am I asking the consult agent to help with?
   - What specific outcome do I want?
   - Is my request clear and specific enough?
   - What might I be missing in my request?
   - What specific problem am I trying to solve?
   - Have I provided all relevant context and constraints?

2. **📊 PROJECT CONTEXT**
   - What is the current state of the project/feature I'm working on?
   - What have I already tried or implemented?
   - What specific problem am I trying to solve?
   - What are my current assumptions and conclusions?
   - Have I considered previous attempts or alternative solutions?
   - What assumptions am I making?

3. **🔍 FILE IDENTIFICATION**
   - What files have I been working with?
   - What files contain the current implementation?
   - What files show the problem or issue I'm facing?
   - What files would help the consult agent understand the project structure?
   - What files contain relevant examples or patterns?
   - What files demonstrate the current system architecture?

4. **🔍 SELF-REVIEW**
   - Am I making any assumptions that might be wrong?
   - Have I considered all the relevant factors?
   - Is my request clear and specific enough?
   - What might I be missing?
   - Have I done enough research to ask an informed question?
   - Have I identified potential gaps in understanding?

5. **📦 CONTEXT PACKAGING**
   - What context would I need if I were the consult agent?
   - What information am I taking for granted that the consult agent won't know?
   - What files should I include as attachments?
   - What specific details should I mention in my prompt?
   - What constraints or requirements should I explicitly state?

### **📂 MANDATORY FILE INCLUSION GUIDELINES**

**You MUST include these files when relevant:**

#### **For Code Generation Requests:**
- **Current implementation files** (the code you're working on)
- **Related component files** (similar patterns or dependencies)
- **Configuration files** (package.json, tsconfig.json, etc.)
- **Error logs or messages** (if debugging)
- **Test files** (if they exist)

#### **For Architecture Planning Requests:**
- **Current system architecture files** (diagrams, configs)
- **Dependency files** (package.json, requirements.txt, etc.)
- **Environment configuration** (docker files, deployment configs)
- **Existing documentation** (README, API docs, etc.)

#### **For Debugging Requests:**
- **The problematic code file**
- **Error messages and logs**
- **Related files that might be involved**
- **Test files that reproduce the issue**
- **Environment configuration**

#### **For Documentation Requests:**
- **Current documentation files**
- **Code files being documented**
- **Project structure files**
- **Existing examples or templates**

### **✅ QUALITY VALIDATION CHECKLIST**

**Before submitting, validate your request:**

- [ ] **Clear and specific**: Can someone else understand exactly what I want?
- [ ] **Complete context**: Have I provided all necessary background information?
- [ ] **Relevant files**: Have I included all files the consult agent needs to see?
- [ ] **No assumptions**: Have I explained things the consult agent won't know?
- [ ] **Specific outcome**: Do I know exactly what I want as a result?
- [ ] **Self-reviewed**: Have I caught any obvious mistakes in my own thinking?
- [ ] **Ritual completed**: Have I completed all 5 steps of the thinking tool ritual?
- [ ] **Comprehensive answers**: Do my ritual responses address all checklist questions?
- [ ] **File attachments**: Have I included all files identified during the ritual?
- [ ] **Request refinement**: Have I refined my request based on ritual insights?

### **📋 TEMPLATE FOR RITUAL COMPLETION**

**Use this template structure for your thinking tool ritual:**

```python
# Step 1: Initial Assessment
mcp_thinking_sequentialthinking({
    "thought": "REQUEST CLARITY: [Define your specific request and desired outcome]",
    "nextThoughtNeeded": True,
    "thoughtNumber": 1,
    "totalThoughts": 5
})

# Step 2: Project Context
mcp_thinking_sequentialthinking({
    "thought": "PROJECT CONTEXT: [Current state, what you've tried, assumptions, constraints]",
    "nextThoughtNeeded": True,
    "thoughtNumber": 2,
    "totalThoughts": 5
})

# Step 3: File Identification
mcp_thinking_sequentialthinking({
    "thought": "FILE IDENTIFICATION: [List all relevant files to include]",
    "nextThoughtNeeded": True,
    "thoughtNumber": 3,
    "totalThoughts": 5
})

# Step 4: Self-Review
mcp_thinking_sequentialthinking({
    "thought": "SELF-REVIEW: [Check assumptions, identify gaps, validate completeness]",
    "nextThoughtNeeded": True,
    "thoughtNumber": 4,
    "totalThoughts": 5
})

# Step 5: Final Packaging
mcp_thinking_sequentialthinking({
    "thought": "CONTEXT PACKAGING: [Final request formulation with all necessary details]",
    "nextThoughtNeeded": False,
    "thoughtNumber": 5,
    "totalThoughts": 5
})
```

## Development Pipeline Integration

### **1. Requirement Analysis**
- Use consult agent for initial planning and requirements gathering
- Define clear objectives, constraints, and success criteria
- Identify potential risks and mitigation strategies
- Create comprehensive project scope and timeline

### **2. Implementation**
- Generate production-ready code with proper error handling
- Include comprehensive testing strategies
- Ensure security and performance considerations
- Follow best practices and coding standards

### **3. Testing**
- Create comprehensive test strategies and frameworks
- Define testing methodologies and coverage requirements
- Plan integration and end-to-end testing approaches
- Establish quality gates and validation criteria

### **4. Documentation**
- Generate user and technical documentation
- Create API references and usage examples
- Develop deployment and operational procedures
- Establish maintenance and troubleshooting guides

### **5. Deployment**
- Plan deployment and operational procedures
- Design monitoring and observability strategies
- Create rollback and disaster recovery plans
- Establish operational runbooks and procedures

## Autonomous Agent Integration

### **Prompt Generation**
- Use consult agent to create detailed prompts for other agents
- Ensure consistency across agent interactions
- Optimize prompts for specific agent capabilities
- Maintain context and continuity across agent workflows

### **Quality Assurance**
- Leverage critic suggestions for validation
- Review and address quality concerns
- Ensure production readiness and best practices
- Validate architectural decisions and implementation choices

### **Iterative Improvement**
- Use multiple iterations for refinement
- Incorporate feedback and suggestions
- Continuously improve implementation quality
- Maintain consistency across iterations

## Intelligent Parameter Analysis Workflow

### **How It Works**

1. **Request Analysis**: When you don't specify parameters, the gpt-5-nano agent analyzes your request
2. **Context Consideration**: It considers your prompt, artifact type, and any attached files
3. **Optimal Selection**: It determines the best values for `iterate`, `critic_enabled`, and `model`
4. **Reasoning Provided**: You get detailed explanations for each parameter choice
5. **User Override Support**: You can still override any parameter if needed

### **Enhanced Gatekeeper Functionality**

The gpt-5-nano agent now acts as an **intelligent gatekeeper** that can:

#### **📊 Project Intelligence Access**
- **Automatic Access**: Gets project intelligence and project map files automatically
- **Context Analysis**: Determines if project context is relevant to your request
- **Smart Filtering**: Decides whether to include project intelligence in the main model context

#### **🔗 Dynamic File Dependency Analysis**
- **Auto-Attach Script**: Lightweight script automatically parses project map to find related files
- **Pre-Attachment**: All related files are attached before nano analysis
- **Nano Filtering**: Nano decides which files to keep or remove from the pre-attached list
- **Efficient Process**: Less cognitively intense - nano focuses on filtering, not discovery
- **Project Map Integration**: Uses actual project structure data for accurate file relationships

#### **📝 Request Enhancement**
- **Request Improvement**: Can rewrite/improve your request for better results
- **Missing Information**: Identifies important information you might have missed
- **Context Pollution Prevention**: Filters out unnecessary context that would pollute the main model

#### **🎛️ Intelligent Context Management**
- **Selective Inclusion**: Decides which context to send to the main model (o3)
- **Project Intelligence**: Include only if relevant to architecture, system design, or project patterns
- **Project Map**: Include only if file structure, dependencies, or imports matter
- **Dynamic Files**: Include only files that are actually needed for the analysis
- **Automatic File Optimization**: Intelligently manages the file list based on dependencies

### **Gatekeeper Control**

You can control whether the intelligent gatekeeper is enabled:

#### **✅ Enable Gatekeeper (Default)**
```python
# Gatekeeper is enabled by default
mcp_consult_agent_consult({
    "prompt": "Create a React authentication component",
    "session_id": "auth_001"
    # Gatekeeper will analyze and optimize everything
})

# Explicitly enable gatekeeper
mcp_consult_agent_consult({
    "prompt": "Create a React authentication component",
    "session_id": "auth_001",
    "gatekeeper_enabled": True  # Explicitly enable
})
```

#### **❌ Disable Gatekeeper**
```python
# Disable gatekeeper and use conservative defaults
mcp_consult_agent_consult({
    "prompt": "Create a React authentication component",
    "session_id": "auth_001",
    "gatekeeper_enabled": False  # Disable gatekeeper
    # Will use conservative defaults: iterate=1, critic_enabled=true, model=o3
})
```

## Session Memory Architecture

The consult agent maintains:
- **Conversation History**: Last 3 exchanges per session
- **Session Timeout**: 1 hour of inactivity
- **Context Injection**: Previous Q&A included in new requests
- **Automatic Cleanup**: Expired sessions are removed

### **Session Management Best Practices**

#### **1. Track Sessions Locally**
```python
# Maintain session state in your agent
sessions = {
    "current_project": "ecommerce_platform",
    "active_sessions": {
        "auth_system": "ecommerce_auth_001",
        "payment_flow": "ecommerce_payment_001",
        "api_docs": "ecommerce_docs_001"
    }
}
```

#### **2. Use Descriptive Session IDs**
```python
# Good: Specific and descriptive
"react_component_library_001"
"microservices_architecture_001"

# Bad: Generic and unclear
"test_001"
"session_1"
"temp_001"
```

#### **3. Version Sessions for Iterations**
```python
# First iteration
"auth_service_001"

# Second iteration (refinements)
"auth_service_002"

# Major redesign
"auth_service_003"
```

#### **4. Reset Sessions When Needed**
```python
# When context becomes polluted or outdated
mcp_consult_agent_consult({
    "prompt": "Let's start fresh with a new approach...",
    "session_id": "auth_service_004"  # New session for fresh start
})
```

## Interactive Response Handling Workflow

### **📋 Response Type Detection**

The consult agent may respond with different types of responses. You MUST detect and handle each type appropriately:

#### **Response Types:**
- **FINAL**: Complete response ready for use
- **QUESTIONS**: Agent needs more information
- **CONCERNS**: Agent has identified potential issues
- **CLARIFICATION**: Agent needs specific details clarified

#### **Detection Logic:**
```python
def extract_response_type(response_text):
    """Extract response type from consult agent response"""
    lines = response_text.strip().split('\n')
    first_line = lines[0].strip()

    if first_line.startswith("**FINAL:**"):
        return "FINAL"
    elif first_line.startswith("**QUESTIONS:**"):
        return "QUESTIONS"
    elif first_line.startswith("**CONCERNS:**"):
        return "CONCERNS"
    elif first_line.startswith("**CLARIFICATION:**"):
        return "CLARIFICATION"
    else:
        return "FINAL"  # Default to final response
```

### **🔄 Multi-Turn Interaction Workflow**

#### **When You Receive Questions/Concerns/Clarification:**

1. **Analyze the Response**: Extract the questions, concerns, or clarification requests
2. **Gather Required Information**: Use the thinking tool to identify what additional information is needed
3. **Prepare Follow-up**: Structure your response to address all points raised
4. **Make Follow-up Call**: Use the same session_id to maintain context

#### **Follow-up Call Structure:**
```python
# First call - Analysis and Questions
response1 = mcp_consult_agent_consult({
    "prompt": "Help me create a React auth component",
    "session_id": "auth_component_001"
})
# Returns: "QUESTIONS: 1. What auth method? 2. Existing utilities?..."

# Second call - Provide additional info
response2 = mcp_consult_agent_consult({
    "prompt": "We're using JWT, have existing utilities in /utils/auth.ts, need login/logout",
    "session_id": "auth_component_001"  # Same session ID
})
# Returns: "FINAL: Here's your React auth component..."
```

### **📋 Response Handling Checklist**

#### **For QUESTIONS Responses:**
- [ ] Extract all questions from the response
- [ ] Use thinking tool to identify what information is needed
- [ ] Gather any missing files or context
- [ ] Structure a comprehensive follow-up response
- [ ] Make follow-up call with same session_id

#### **For CONCERNS Responses:**
- [ ] Review all flagged concerns
- [ ] Assess whether concerns are valid
- [ ] Provide additional context to address concerns
- [ ] Consider alternative approaches if needed
- [ ] Make follow-up call with same session_id

#### **For CLARIFICATION Responses:**
- [ ] Identify what specifically needs clarification
- [ ] Provide more specific details about your request
- [ ] Include relevant examples or context
- [ ] Make follow-up call with same session_id

#### **For FINAL Responses:**
- [ ] Review the complete response
- [ ] Validate it meets your requirements
- [ ] Proceed with implementation or use as directed

### **🎯 Best Practices for Interactive Sessions**

1. **Maintain Session Context**: Always use the same session_id for follow-up calls
2. **Be Comprehensive**: Address all questions/concerns in your follow-up
3. **Provide Context**: Include relevant files and background information
4. **Be Specific**: Give concrete details rather than vague descriptions
5. **Follow the Flow**: Let the consult agent guide the conversation naturally

## Validation Framework

### **Pre-Execution Checklist**
- [ ] Clear, specific prompt with all requirements
- [ ] Appropriate artifact type selected
- [ ] Session ID follows naming convention
- [ ] Quality control enabled for production code
- [ ] Iteration count appropriate for task complexity

### **Post-Execution Validation**
- [ ] Response addresses all requirements
- [ ] Critic suggestions reviewed and addressed
- [ ] Production readiness confirmed
- [ ] Best practices followed
- [ ] Session continuity maintained

### **Quality Gates**
- **Code Quality**: Type safety, error handling, logging, tests
- **Architecture Quality**: Scalability, maintainability, security
- **Documentation Quality**: Completeness, clarity, examples
- **Workflow Quality**: Automation, monitoring, operational readiness

## Success Metrics

### **Response Quality Indicators**
- **Completeness**: All requirements addressed
- **Production Readiness**: Error handling, logging, type safety
- **Best Practices**: Current standards and patterns
- **Critic Approval**: Minimal or actionable critic suggestions

### **Efficiency Metrics**
- **Prompt Clarity**: Specific, actionable requests
- **Iteration Effectiveness**: Meaningful improvements per iteration
- **Session Continuity**: Logical task progression within sessions
