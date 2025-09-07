# Code Modification Input Form

## Modification Metadata
- **Modification ID**: `MOD-YYYY-MM-DD-001`
- **Type**: `[feature_add|feature_modify|feature_remove|refactor|optimization|integration]`
- **Priority**: `[critical|high|medium|low]`
- **Requestor**: `[name/team requesting the modification]`
- **Description**: `[20-1000 characters, clear description of the modification]`
- **Business Justification**: `[why this modification is needed]`

## Target Analysis
### Target Files
For each file to be modified:
- **Path**: `[file path]`
- **Type**: `[source|test|config|documentation|script]`
- **Purpose**: `[what this file does]`
- **Lines of Code**: `[number]`
- **Complexity Score**: `[cyclomatic complexity]`
- **Last Modified**: `[date]`

### Current State
- **Version**: `[current version]`
- **Git Branch**: `[current branch]`
- **Commit Hash**: `[current commit]`
- **Deployment Status**: `[current deployment status]`
- **Known Issues**:
  - `[issue 1]`
  - `[issue 2]`

### Dependencies
- **Internal Dependencies**: `[list of internal dependencies]`
- **External Dependencies**: `[list of external dependencies]`
- **Database Schema**: `[description of current schema]`
- **API Contracts**: `[list of API contracts]`
- **Configuration Files**: `[list of config files]`

## Change Requirements
### Functional Changes
For each functional change:
- **ID**: `FC-001, FC-002, etc.`
- **Description**: `[what functionality is changing]`
- **Acceptance Criteria**:
  - `[criterion 1]`
  - `[criterion 2]`
- **User Story**: `[As a user, I want... so that...]`
- **Business Value**: `[why this change adds value]`

### Technical Changes
For each technical change:
- **ID**: `TC-001, TC-002, etc.`
- **Description**: `[what technical aspect is changing]`
- **Implementation Approach**: `[how the change will be implemented]`
- **Affected Components**: `[list of components affected]`
- **New Dependencies**: `[new dependencies required]`
- **Removed Dependencies**: `[dependencies being removed]`

### Backward Compatibility
- **Required**: `[yes/no]`
- **Breaking Changes**:
  - `[breaking change 1]`
  - `[breaking change 2]`
- **Migration Required**: `[yes/no]`
- **Migration Plan**: `[description of migration strategy]`

## Impact Assessment
### Affected Systems
For each affected system:
- **System Name**: `[name of system]`
- **Impact Level**: `[high|medium|low|none]`
- **Impact Description**: `[how this system is affected]`
- **Mitigation Required**: `[yes/no]`

### Risk Analysis
#### Technical Risks
For each technical risk:
- **Risk**: `[description of risk]`
- **Probability**: `[high|medium|low]`
- **Impact**: `[high|medium|low]`
- **Mitigation**: `[how to mitigate this risk]`

#### Business Risks
For each business risk:
- **Risk**: `[description of risk]`
- **Probability**: `[high|medium|low]`
- **Impact**: `[high|medium|low]`
- **Mitigation**: `[how to mitigate this risk]`

### Performance Impact
- **Expected Changes**: `[description of performance changes]`
- **Performance Tests Required**: `[yes/no]`
- **Monitoring Requirements**: `[list of metrics to monitor]`

## Validation Plan
### Testing Strategy
#### Test Types
For each test type:
- **Type**: `[unit|integration|system|regression|performance|security]`
- **Scope**: `[what will be tested]`
- **Criteria**: `[success criteria]`
- **Automated**: `[yes/no]`
- **Estimated Effort**: `[time estimate]`

#### Test Environment
- **Environment Type**: `[development|staging|production]`
- **Data Requirements**: `[description of test data needed]`
- **Setup Requirements**:
  - `[requirement 1]`
  - `[requirement 2]`

#### Acceptance Criteria
- `[acceptance criterion 1]`
- `[acceptance criterion 2]`
- `[acceptance criterion 3]`

### Deployment Plan
- **Deployment Strategy**: `[blue_green|rolling|canary|big_bang]`
- **Rollback Trigger Conditions**:
  - `[condition 1]`
  - `[condition 2]`
- **Rollback Steps**:
  - `[step 1]`
  - `[step 2]`
- **Estimated Rollback Time**: `[time estimate]`

#### Monitoring Plan
- **Key Metrics**:
  - `[metric 1]`
  - `[metric 2]`
- **Alert Conditions**:
  - `[condition 1]`
  - `[condition 2]`
- **Monitoring Duration**: `[how long to monitor]`

### Documentation Updates
- **Required Updates**:
  - `[document 1]`
  - `[document 2]`
- **New Documentation**:
  - `[new doc 1]`
  - `[new doc 2]`
- **Deprecated Documentation**:
  - `[deprecated doc 1]`
  - `[deprecated doc 2]`

## Constraints
### Timeline
- **Deadline**: `[date]`
- **Development Time**: `[time estimate]`
- **Testing Time**: `[time estimate]`
- **Deployment Window**: `[time window]`

### Resources
- **Development Team**: `[list of team members]`
- **Testing Team**: `[list of testers]`
- **Infrastructure Requirements**: `[list of infrastructure needs]`

### Compatibility
- **Version Compatibility**: `[compatibility requirements]`
- **Platform Requirements**: `[platform constraints]`
- **Third Party Integrations**: `[integration requirements]`

---

**Validation Checklist**:
- [ ] All required fields completed
- [ ] Modification ID follows naming convention
- [ ] Target files are clearly identified
- [ ] Impact assessment is comprehensive
- [ ] Risk analysis includes mitigation strategies
- [ ] Testing strategy covers all change types
- [ ] Deployment plan includes rollback strategy
- [ ] Timeline is realistic with given resources
