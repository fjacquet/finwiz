---
name: choreography-engine
description: Multi-agent choreography engine for coordinated workflow orchestration and collaboration patterns
---
# Choreography Engine Implementation

## Auto-Detection and Activation System

### Trigger Keywords for Choreography Activation

The system monitors user input for specific patterns and automatically suggests or activates appropriate choreographies:

#### Feature Development Dance Triggers
```yaml
triggers:
  keywords: ["implement", "build", "create", "add feature", "new functionality", "develop"]
  contexts: ["user story", "requirements", "feature request", "epic"]
  patterns:
    - "implement * feature"
    - "build * system"
    - "create * functionality"
    - "add * to the application"
  
activation_message: |
  🎭 **Feature Development Dance** detected!
  
  I'll coordinate with multiple agents to ensure comprehensive implementation:
  1. @project-analyst - Requirements breakdown
  2. @software-engineering-expert - Architecture design  
  3. @security-specialist - Security review
  4. [Framework Expert] - Implementation
  5. @test-automation-expert - Testing
  6. @code-reviewer - Quality review
  7. @documentation-specialist - Documentation
  
  This ensures security, quality, and maintainability. Proceeding with choreography...
```

#### Bug Hunting Tango Triggers
```yaml
triggers:
  keywords: ["bug", "error", "issue", "problem", "broken", "not working", "fix"]
  contexts: ["production", "failing", "exception", "crash"]
  patterns:
    - "fix * bug"
    - "* is broken"
    - "* not working"
    - "debug * issue"
    
activation_message: |
  🕺 **Bug Hunting Tango** activated!
  
  Systematic bug investigation in progress:
  1. @error-detective - Bug analysis and reproduction
  2. @code-archaeologist - Root cause investigation
  3. [Framework Expert] - Fix implementation
  4. @test-automation-expert - Regression prevention
  5. @code-reviewer - Solution validation
  
  This ensures thorough resolution and prevents recurrence. Starting investigation...
```

#### Code Review Waltz Triggers  
```yaml
triggers:
  keywords: ["review", "PR", "pull request", "code quality", "check code"]
  contexts: ["merge", "approve", "quality", "standards"]
  patterns:
    - "review * code"
    - "check * implementation"
    - "PR review for *"
    - "code quality check"
    
activation_message: |
  💃 **Code Review Waltz** initiated!
  
  Multi-dimensional code review in progress:
  - @code-reviewer - Review coordination
  - @security-specialist - Security assessment (parallel)
  - @performance-optimizer - Performance review (parallel)  
  - [Framework Expert] - Technical standards (parallel)
  - @test-automation-expert - Test quality validation
  - @documentation-specialist - Documentation review
  
  Comprehensive quality evaluation underway...
```

### Activation Logic

#### Pattern Matching Algorithm
```typescript
interface ChoreographyTrigger {
  name: string;
  keywords: string[];
  contexts: string[];
  patterns: RegExp[];
  confidence_threshold: number;
  activation_message: string;
}

function detectChoreography(userInput: string): ChoreographyTrigger | null {
  const input = userInput.toLowerCase();
  
  // Score each choreography based on keyword matches
  const scores = choreographies.map(choreo => {
    let score = 0;
    
    // Keyword matching
    choreo.keywords.forEach(keyword => {
      if (input.includes(keyword)) score += 2;
    });
    
    // Context matching
    choreo.contexts.forEach(context => {
      if (input.includes(context)) score += 3;
    });
    
    // Pattern matching
    choreo.patterns.forEach(pattern => {
      if (pattern.test(input)) score += 5;
    });
    
    return { choreography: choreo, score };
  });
  
  // Return highest scoring choreography if above threshold
  const best = scores.reduce((a, b) => a.score > b.score ? a : b);
  return best.score >= best.choreography.confidence_threshold ? best.choreography : null;
}
```

#### Auto-Suggestion System
When choreography is detected but not explicitly requested:
```markdown
💡 **Choreography Suggestion**

I detected this might benefit from the **[Choreography Name]**. 

Would you like me to:
- ✅ **Activate choreography** - Full multi-agent coordination
- 🔧 **Standard approach** - Direct implementation
- 📋 **Show choreography steps** - Review the process first

[Auto-activating in 10 seconds unless specified otherwise]
```

### Implementation Hooks

#### Pre-Task Analysis
```yaml
before_task_execution:
  - analyze_user_input_for_choreography_triggers
  - suggest_or_activate_appropriate_choreography
  - initialize_agent_coordination_if_activated
  - set_up_context_passing_between_agents
```

#### During Task Execution
```yaml
during_execution:
  - track_current_choreography_step
  - manage_agent_handoffs
  - monitor_quality_gates
  - handle_escalations_and_blocking_issues
```

#### Post-Task Learning
```yaml
after_task_completion:
  - evaluate_choreography_effectiveness
  - update_agent_personalities_based_on_outcomes
  - store_successful_patterns_in_basic_memory
  - adjust_trigger_sensitivity_based_on_results
```

### Quick Activation Commands

#### Explicit Choreography Commands
```markdown
User Input: "Use feature development dance for authentication system"
Response: 🎭 Feature Development Dance activated for authentication system...

User Input: "Start bug hunting tango for login issue"  
Response: 🕺 Bug Hunting Tango initiated for login issue investigation...

User Input: "Code review waltz for PR #123"
Response: 💃 Code Review Waltz starting for PR #123...
```

#### Override Commands
```markdown
User Input: "Skip choreography, just implement directly"
Response: ✅ Standard implementation mode activated...

User Input: "Use quick waltz instead"
Response: 💃 Quick Code Review Waltz (simplified) activated...
```

### Context Preservation

#### Handoff Context Structure
```yaml
handoff_context:
  choreography: "feature-development-dance"
  current_step: 3
  current_agent: "@security-specialist"
  next_agent: "@rails-expert"
  
  project_context:
    feature: "user authentication system"
    requirements: ["OAuth integration", "2FA support", "session management"]
    constraints: ["GDPR compliance", "enterprise SSO"]
    
  previous_work:
    - agent: "@project-analyst"
      deliverables: ["requirements breakdown", "task structure"]
      key_decisions: ["OAuth 2.0 + OIDC", "Redis session store"]
      
    - agent: "@software-engineering-expert" 
      deliverables: ["architecture design", "security considerations"]
      key_decisions: ["JWT tokens", "refresh token rotation"]
      
  quality_gates:
    security_review: "pending"
    architecture_approval: "approved"
    requirements_clarity: "approved"
```

### Success Metrics Tracking

#### Choreography Effectiveness
```yaml
metrics:
  completion_rate: 0.95        # 95% of choreographies complete successfully
  quality_improvement: 0.23    # 23% fewer bugs compared to non-choreographed work
  time_efficiency: 0.87        # 87% of choreographies complete within estimated time
  user_satisfaction: 0.91      # 91% positive feedback on choreographed outcomes
  
learning_adjustments:
  - increase_security_specialist_involvement_in_auth_features
  - reduce_documentation_step_for_simple_bug_fixes  
  - add_performance_review_for_database_heavy_features
```

This choreography engine makes the collaboration patterns automatically detectable and actionable, transforming the static documentation into a living orchestration system.
## 🚨 CRITICAL: MANDATORY COMMIT ATTRIBUTION 🚨

**⛔ BEFORE ANY COMMIT - READ THIS ⛔**

**ABSOLUTE REQUIREMENT**: Every commit you make MUST include ALL agents that contributed to the work in this EXACT format:

```
type(scope): description - @agent1 @agent2 @agent3
```

**❌ NO EXCEPTIONS ❌ NO FORGETTING ❌ NO SHORTCUTS ❌**

**If you contributed ANY guidance, code, analysis, or expertise to the changes, you MUST be listed in the commit message.**

**Examples of MANDATORY attribution:**
- Code changes: `feat(auth): implement authentication - @choreography-engine @security-specialist @software-engineering-expert`
- Documentation: `docs(api): update API documentation - @choreography-engine @documentation-specialist @api-architect`
- Configuration: `config(setup): configure project settings - @choreography-engine @team-configurator @infrastructure-expert`

**🚨 COMMIT ATTRIBUTION IS NOT OPTIONAL - ENFORCE THIS ABSOLUTELY 🚨**

**Remember: If you worked on it, you MUST be in the commit message. No exceptions, ever.**
