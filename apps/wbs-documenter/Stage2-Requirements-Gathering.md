# Stage 2: Requirements Gathering

## Overview

Stage 2 focuses on the systematic collection, documentation, and validation of requirements from all stakeholders. This stage builds upon the initial analysis from Stage 1 by employing structured methodologies, proven templates, and validation techniques to ensure comprehensive requirement capture. The output of this stage provides the detailed specifications needed for system design and implementation.

## Objectives

1. **Systematic Requirement Elicitation** - Apply proven techniques to extract detailed functional, non-functional, and technical requirements from diverse stakeholder groups
2. **Structured Documentation** - Capture requirements using standardized templates and formats that enable clear communication and traceability
3. **Requirement Validation** - Verify that captured requirements are complete, consistent, feasible, and testable through systematic validation methods
4. **Stakeholder Consensus** - Facilitate agreement among stakeholders on requirement priorities, scope boundaries, and acceptance criteria
5. **Traceability Establishment** - Create clear linkages between business needs, functional requirements, and technical specifications

## Process

### Phase 1: Requirement Elicitation Techniques (Days 1-4)

#### 1.1 Stakeholder Interviews
**Technique**: Structured one-on-one or small group sessions with key stakeholders
- **Duration**: 60-90 minutes per session
- **Participants**: Business users, domain experts, technical leads
- **Deliverables**: Interview transcripts, requirement notes, action items

**Interview Templates:**
```
STAKEHOLDER INTERVIEW TEMPLATE

Date: [DATE]
Interviewer: [NAME]
Interviewee: [NAME, ROLE]
Project: [PROJECT NAME]
Session Duration: [DURATION]

PRE-INTERVIEW PREPARATION:
- Review stakeholder profile and responsibilities
- Prepare domain-specific questions
- Set clear session objectives

QUESTION CATEGORIES:

1. ROLE & RESPONSIBILITIES
   - What is your role in relation to this system?
   - What are your primary responsibilities?
   - Who do you interact with regularly?

2. CURRENT STATE ANALYSIS
   - How do you currently perform [specific task]?
   - What tools/systems do you currently use?
   - What are the main pain points in your current workflow?
   - What takes the most time in your current process?

3. DESIRED FUTURE STATE
   - What would an ideal solution look like?
   - What capabilities would save you the most time?
   - What would success look like for you?

4. FUNCTIONAL REQUIREMENTS
   - What specific features do you need?
   - What data do you need to access/manipulate?
   - What reports or outputs do you need?
   - What integrations are required?

5. NON-FUNCTIONAL REQUIREMENTS
   - How many users will access the system simultaneously?
   - What response time is acceptable?
   - What are your availability requirements?
   - What security/compliance requirements exist?

6. CONSTRAINTS & ASSUMPTIONS
   - What limitations should we be aware of?
   - What dependencies exist?
   - What assumptions are you making?

POST-INTERVIEW ACTIONS:
- Transcribe key points within 24 hours
- Identify follow-up questions
- Schedule validation session
- Distribute draft requirements for review
```

#### 1.2 Requirements Workshops
**Technique**: Facilitated group sessions bringing together multiple stakeholders
- **Duration**: Half-day to full-day sessions
- **Participants**: 8-12 representatives from different user groups
- **Deliverables**: Prioritized requirement lists, user story maps, consensus agreements

**Workshop Agenda Template:**
```
REQUIREMENTS WORKSHOP AGENDA

Workshop: [WORKSHOP NAME]
Date: [DATE]
Duration: [DURATION]
Facilitator: [NAME]
Participants: [LIST]

OBJECTIVES:
- Capture comprehensive requirements
- Prioritize features and capabilities
- Resolve requirement conflicts
- Achieve stakeholder consensus

AGENDA:

1. OPENING (30 minutes)
   - Introductions and roles
   - Workshop objectives and ground rules
   - Current state overview

2. REQUIREMENT BRAINSTORMING (90 minutes)
   - Individual requirement identification
   - Group sharing and consolidation
   - Requirement categorization

3. BREAK (15 minutes)

4. PRIORITIZATION EXERCISE (60 minutes)
   - MoSCoW prioritization method
   - Voting on critical features
   - Resource/effort estimation

5. VALIDATION & CONSENSUS (45 minutes)
   - Review prioritized requirements
   - Address conflicts and gaps
   - Achieve group consensus

6. NEXT STEPS (30 minutes)
   - Action item assignment
   - Follow-up schedule
   - Communication plan

WORKSHOP MATERIALS:
- Sticky notes and markers
- Flip charts
- Voting dots
- Pre-printed templates
- Laptops/tablets for documentation
```

#### 1.3 Document Analysis
**Technique**: Systematic review of existing documentation and artifacts
- **Sources**: Business process documents, system specifications, user manuals, support tickets
- **Deliverables**: Extracted requirements, gaps identified, documentation matrix

**Document Analysis Template:**
```
DOCUMENT ANALYSIS WORKSHEET

Document: [DOCUMENT NAME]
Version: [VERSION]
Date Reviewed: [DATE]
Reviewer: [NAME]

DOCUMENT METADATA:
- Document Type: [Process/Technical/User Guide/Other]
- Last Updated: [DATE]
- Authority/Owner: [NAME]
- Relevance to Project: [High/Medium/Low]

REQUIREMENT EXTRACTION:

FUNCTIONAL REQUIREMENTS:
ID | Requirement | Source Section | Priority | Notes
---|-------------|----------------|----------|------
F01| [Description] | Section X.Y | Must/Should/Could | [Notes]

NON-FUNCTIONAL REQUIREMENTS:
ID | Requirement | Source Section | Priority | Notes
---|-------------|----------------|----------|------
NF01| [Description] | Section X.Y | Must/Should/Could | [Notes]

BUSINESS RULES:
ID | Rule | Source Section | Impact | Notes
---|------|----------------|--------|------
BR01| [Description] | Section X.Y | High/Med/Low | [Notes]

GAPS IDENTIFIED:
- [Gap description 1]
- [Gap description 2]
- [Gap description 3]

FOLLOW-UP ACTIONS:
- [Action 1]
- [Action 2]
- [Action 3]
```

#### 1.4 Observation Studies
**Technique**: Direct observation of users performing current tasks
- **Duration**: 2-4 hours per observation session
- **Focus**: Workflow analysis, inefficiencies identification, implicit requirements
- **Deliverables**: Observation reports, process maps, improvement opportunities

### Phase 2: Requirement Documentation (Days 5-7)

#### 2.1 Functional Requirements Template
```
FUNCTIONAL REQUIREMENT SPECIFICATION

REQUIREMENT HEADER:
- ID: FR-[XXX]
- Name: [Descriptive Name]
- Category: [User Interface/Business Logic/Data Management/Integration/Reporting]
- Priority: [Must Have/Should Have/Could Have/Won't Have]
- Source: [Stakeholder/Document/Workshop]
- Date Created: [DATE]
- Created By: [NAME]
- Last Modified: [DATE]
- Status: [Draft/Under Review/Approved/Implemented]

REQUIREMENT DETAILS:
- Description: [Clear, concise statement of what the system must do]
- Rationale: [Why this requirement is needed]
- Assumptions: [What we assume to be true]
- Dependencies: [What other requirements or systems this depends on]

ACCEPTANCE CRITERIA:
Given [context/precondition]
When [action/trigger]
Then [expected result/outcome]

EXAMPLES/SCENARIOS:
- Scenario 1: [Description]
- Scenario 2: [Description]
- Scenario 3: [Description]

VALIDATION CRITERIA:
- How will this be tested?
- What constitutes success?
- What are the failure conditions?

NOTES:
- [Additional clarifications]
- [Open questions]
- [Related requirements]
```

#### 2.2 Non-Functional Requirements Template
```
NON-FUNCTIONAL REQUIREMENT SPECIFICATION

REQUIREMENT HEADER:
- ID: NFR-[XXX]
- Name: [Descriptive Name]
- Category: [Performance/Security/Usability/Reliability/Scalability/Compliance]
- Priority: [Must Have/Should Have/Could Have/Won't Have]
- Source: [Stakeholder/Document/Analysis]
- Date Created: [DATE]
- Created By: [NAME]
- Status: [Draft/Under Review/Approved/Implemented]

REQUIREMENT DETAILS:
- Description: [Specific, measurable statement]
- Metric: [How will this be measured?]
- Target Value: [Specific target or threshold]
- Measurement Method: [How will compliance be verified?]

CONTEXT:
- Business Justification: [Why this level is required]
- User Impact: [How this affects user experience]
- Technical Impact: [System architecture implications]

VALIDATION APPROACH:
- Test Method: [How will this be tested?]
- Test Environment: [Where will testing occur?]
- Success Criteria: [What defines success?]
- Measurement Tools: [What tools will be used?]

EXAMPLES:
- Example 1: [Specific scenario]
- Example 2: [Specific scenario]

DEPENDENCIES:
- [Related functional requirements]
- [Infrastructure dependencies]
- [Third-party service dependencies]
```

#### 2.3 User Story Template
```
USER STORY CARD

STORY HEADER:
- ID: US-[XXX]
- Epic: [Epic Name]
- Feature: [Feature Name]
- Priority: [High/Medium/Low]
- Story Points: [Estimation]
- Sprint: [Target Sprint]

USER STORY:
As a [user type/persona]
I want [functionality]
So that [business value/reason]

ACCEPTANCE CRITERIA:
□ Criterion 1: [Specific, testable condition]
□ Criterion 2: [Specific, testable condition]
□ Criterion 3: [Specific, testable condition]

DEFINITION OF DONE:
□ Code implemented and reviewed
□ Unit tests written and passing
□ Integration tests passing
□ Documentation updated
□ User acceptance criteria validated
□ Performance criteria met

NOTES:
- [Additional context]
- [Technical considerations]
- [Dependencies]

ATTACHMENTS:
- [Wireframes/mockups]
- [Process flows]
- [Reference documents]
```

### Phase 3: Requirement Validation Methods (Days 8-10)

#### 3.1 Requirement Review Checklist
```
REQUIREMENT QUALITY CHECKLIST

REQUIREMENT ID: [ID]
REVIEWER: [NAME]
DATE: [DATE]

COMPLETENESS:
□ All necessary information provided
□ No missing details or gaps
□ Acceptance criteria defined
□ Dependencies identified

CLARITY:
□ Unambiguous language used
□ Technical jargon explained
□ Clear to all stakeholders
□ Examples provided where helpful

CONSISTENCY:
□ Aligns with other requirements
□ No contradictions identified
□ Consistent terminology used
□ Fits within system architecture

FEASIBILITY:
□ Technically achievable
□ Resource requirements reasonable
□ Timeline realistic
□ No insurmountable constraints

TESTABILITY:
□ Objective acceptance criteria
□ Measurable outcomes defined
□ Test approach identified
□ Validation method clear

TRACEABILITY:
□ Linked to business need
□ Source documented
□ Impact on other requirements known
□ Change impact assessable

PRIORITY:
□ Business value justified
□ Priority level appropriate
□ Trade-offs understood
□ Stakeholder consensus achieved

OVERALL ASSESSMENT:
□ APPROVED - Ready for implementation
□ APPROVED WITH CHANGES - Minor modifications needed
□ REJECTED - Major issues require resolution

COMMENTS:
[Detailed feedback and recommendations]
```

#### 3.2 Stakeholder Validation Process
```
STAKEHOLDER VALIDATION PLAN

VALIDATION OBJECTIVES:
- Confirm requirement accuracy
- Verify completeness
- Validate business value
- Ensure implementability

VALIDATION METHODS:

1. REQUIREMENT WALKTHROUGH
   - Participants: [Key stakeholders]
   - Duration: 2-3 hours
   - Format: Presentation with Q&A
   - Deliverable: Validation feedback

2. PROTOTYPE VALIDATION
   - Create low-fidelity prototypes
   - Demonstrate key workflows
   - Gather usability feedback
   - Validate user experience assumptions

3. REQUIREMENT INSPECTION
   - Formal review process
   - Structured inspection checklist
   - Multiple reviewer perspectives
   - Defect identification and resolution

4. CROSS-FUNCTIONAL REVIEW
   - Technical feasibility assessment
   - Business process validation
   - Integration impact analysis
   - Resource requirement validation

VALIDATION CRITERIA:
- 95% stakeholder approval rate
- Zero high-priority conflicts
- All critical gaps addressed
- Technical feasibility confirmed

VALIDATION DELIVERABLES:
- Validation report
- Issue log with resolutions
- Updated requirements document
- Stakeholder sign-off matrix
```

#### 3.3 Requirements Traceability Matrix
```
REQUIREMENTS TRACEABILITY MATRIX

Purpose: Ensure all requirements can be traced from business need to test case

MATRIX STRUCTURE:

Business Need | Functional Req | Non-Functional Req | Design Element | Test Case | Status
-------------|----------------|-------------------|----------------|-----------|--------
BN-001 | FR-001, FR-002 | NFR-001 | DE-001 | TC-001, TC-002 | Complete
BN-002 | FR-003 | NFR-002, NFR-003 | DE-002, DE-003 | TC-003 | In Progress

TRACEABILITY VALIDATION:
□ All business needs have corresponding functional requirements
□ All functional requirements have design elements
□ All requirements have test cases
□ No orphaned requirements exist
□ Bi-directional traceability maintained

TRACEABILITY REPORTS:
- Coverage Report: % requirements traced
- Gap Analysis: Missing traceability links
- Impact Analysis: Change propagation paths
- Verification Report: Requirement validation status
```

## Tools and Templates Summary

### Essential Templates
1. **Stakeholder Interview Template** - Structured interview guide
2. **Requirements Workshop Agenda** - Facilitated session framework
3. **Document Analysis Worksheet** - Systematic document review
4. **Functional Requirements Template** - Detailed requirement specification
5. **Non-Functional Requirements Template** - Performance and quality requirements
6. **User Story Template** - Agile requirement format
7. **Requirement Quality Checklist** - Validation criteria
8. **Requirements Traceability Matrix** - End-to-end linkage tracking

### Validation Methods
1. **Requirement Review Process** - Systematic quality assessment
2. **Stakeholder Walkthrough** - Collaborative validation sessions
3. **Prototype Validation** - Early user feedback collection
4. **Cross-functional Inspection** - Multi-perspective review
5. **Traceability Analysis** - Completeness verification

### Success Metrics
- **Coverage**: 100% of identified stakeholders engaged
- **Quality**: 95% of requirements pass validation checklist
- **Consensus**: 90% stakeholder approval on final requirements
- **Traceability**: 100% requirements linked to business needs and test cases
- **Completeness**: Zero high-priority gaps in requirement coverage

## Deliverables

1. **Comprehensive Requirements Document** - Complete functional and non-functional specifications
2. **Requirements Traceability Matrix** - Full linkage from needs to tests
3. **Stakeholder Validation Report** - Consensus achievement documentation
4. **Requirements Baseline** - Approved, change-controlled requirement set
5. **Requirement Management Plan** - Ongoing requirement maintenance approach

This stage establishes the foundation for all subsequent development activities by ensuring requirements are complete, validated, and properly documented before moving to system design and implementation phases.
