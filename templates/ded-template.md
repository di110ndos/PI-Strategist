# Design & Engineering Document (DED) Template

## Document Information
- **Project Name:** [Project Name]
- **Version:** 1.0
- **Last Updated:** [Date]
- **Author:** [Author Name]
- **Reviewers:** [Reviewer Names]

---

## Epic: [EPIC-001] [Epic Name]

### Epic Description
[Provide a brief description of the epic and its business value]

### Business Objectives
- [Objective 1]
- [Objective 2]

### Success Metrics
- [Metric 1: e.g., "Reduce login time to <2 seconds"]
- [Metric 2: e.g., "Achieve 99.9% uptime"]

---

## Story: [STORY-001] [Story Name]

### Story Description
As a [user type], I want to [action] so that [benefit].

### Acceptance Criteria

**AC-001:** [Specific, measurable criterion]
- Given [precondition]
- When [action]
- Then [expected result with specific metrics]

**AC-002:** [Specific, measurable criterion]
- Given [precondition]
- When [action]
- Then [expected result with specific metrics]

**AC-003:** [Specific, measurable criterion]
- Given [precondition]
- When [action]
- Then [expected result with specific metrics]

### Technical Notes
- [Note 1]
- [Note 2]

### Dependencies
- [Dependency 1]
- [Dependency 2]

### Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | Low/Medium/High | Low/Medium/High | [Mitigation strategy] |

---

## Story: [STORY-002] [Story Name]

### Story Description
As a [user type], I want to [action] so that [benefit].

### Acceptance Criteria

**AC-001:** [Specific, measurable criterion]

**AC-002:** [Specific, measurable criterion]

---

## Tasks

### Task: [TASK-001] [Task Name]
- **Story:** STORY-001
- **Estimate:** 8 hours
- **Assignee:** [Name]
- **Dependencies:** None

### Task: [TASK-002] [Task Name]
- **Story:** STORY-001
- **Estimate:** 4 hours
- **Assignee:** [Name]
- **Dependencies:** TASK-001

---

## Appendix

### Glossary
| Term | Definition |
|------|------------|
| [Term 1] | [Definition] |

### References
- [Reference 1]
- [Reference 2]

---

## Writing Good Acceptance Criteria

### Avoid These Red Flags:
- **Subjective terms:** "fast", "user-friendly", "simple", "robust"
- **Vague metrics:** "high quality", "performant", "scalable"
- **Missing criteria:** "works well", "looks good"
- **Undefined scope:** "comprehensive", "all edge cases", "etc."

### Use Measurable Criteria:
| Instead of... | Write... |
|---------------|----------|
| "The page loads fast" | "The page loads in <2 seconds at 95th percentile" |
| "User-friendly interface" | "Users complete primary action in ≤3 clicks" |
| "Comprehensive validation" | "Validates: email format, MX record, disposable domain blocklist" |
| "Secure authentication" | "Passes OWASP Top 10 with 0 critical/high findings" |
| "Scalable architecture" | "Supports 10,000 concurrent users with <5% latency increase" |
