---
name: workflow-coordinator
description: Workflow coordination system for managing complex multi-agent development processes
---
# Workflow Coordinator

## Multi-Agent Orchestration Engine

### Overview
The Workflow Coordinator manages the execution of choreography patterns, coordinates agent handoffs, maintains context, and ensures quality gates are met throughout multi-agent collaborations.

### Core Orchestration Engine

#### Workflow State Management
```typescript
interface WorkflowState {
  choreography: string;              // "feature-development-dance"
  currentStep: number;               // Current step in choreography
  currentAgent: string;              // "@security-specialist"
  nextAgent: string;                 // "@rails-expert"
  status: 'active' | 'blocked' | 'completed' | 'failed';
  
  context: {
    taskDescription: string;
    requirements: string[];
    constraints: string[];
    decisions: Decision[];
    deliverables: Deliverable[];
  };
  
  qualityGates: {
    [gateName: string]: 'pending' | 'approved' | 'rejected' | 'not_required';
  };
  
  timeline: {
    startTime: Date;
    stepStartTime: Date;
    estimatedCompletion: Date;
    actualStepDurations: number[];
  };
}

class WorkflowCoordinator {
  private activeWorkflows: Map<string, WorkflowState> = new Map();
  
  async startChoreography(choreographyName: string, taskDescription: string): Promise<string> {
    const workflowId = this.generateWorkflowId();
    const choreography = await this.loadChoreography(choreographyName);
    
    const initialState: WorkflowState = {
      choreography: choreographyName,
      currentStep: 0,
      currentAgent: choreography.steps[0].agent,
      nextAgent: choreography.steps[1]?.agent || null,
      status: 'active',
      context: {
        taskDescription,
        requirements: [],
        constraints: [],
        decisions: [],
        deliverables: []
      },
      qualityGates: this.initializeQualityGates(choreography),
      timeline: {
        startTime: new Date(),
        stepStartTime: new Date(),
        estimatedCompletion: this.calculateEstimatedCompletion(choreography),
        actualStepDurations: []
      }
    };
    
    this.activeWorkflows.set(workflowId, initialState);
    await this.executeCurrentStep(workflowId);
    
    return workflowId;
  }
}
```

#### Step Execution Engine
```typescript
async executeCurrentStep(workflowId: string): Promise<void> {
  const workflow = this.activeWorkflows.get(workflowId);
  const choreography = await this.loadChoreography(workflow.choreography);
  const currentStep = choreography.steps[workflow.currentStep];
  
  // Display step initiation
  console.log(`🎭 **${workflow.choreography}** - Step ${workflow.currentStep + 1}/${choreography.steps.length}`);
  console.log(`👤 **${currentStep.agent}** (${currentStep.role}) - ${currentStep.responsibilities[0]}`);
  
  try {
    // Load agent personality
    const personality = await this.loadAgentPersonality(currentStep.agent);
    
    // Prepare agent context
    const agentContext = this.prepareAgentContext(workflow, currentStep);
    
    // Execute agent task with personality
    const result = await this.executeAgentTask(currentStep.agent, agentContext, personality);
    
    // Process agent output
    await this.processStepResult(workflowId, result);
    
    // Check handoff conditions
    if (this.checkHandoffConditions(workflow, currentStep, result)) {
      await this.proceedToNextStep(workflowId);
    } else {
      workflow.status = 'blocked';
      await this.handleBlockedWorkflow(workflowId, result);
    }
    
  } catch (error) {
    workflow.status = 'failed';
    await this.handleWorkflowFailure(workflowId, error);
  }
}

async executeAgentTask(agentName: string, context: AgentContext, personality: PersonalityDimensions): Promise<AgentResult> {
  // This would integrate with Claude Code's agent system
  const baseResponse = await this.callAgent(agentName, context);
  
  // Apply personality transformations
  const personalizedResponse = PersonalityEngine.applyPersonality(baseResponse, personality, context);
  
  return {
    agent: agentName,
    response: personalizedResponse,
    deliverables: this.extractDeliverables(baseResponse),
    decisions: this.extractDecisions(baseResponse),
    qualityGateStatus: this.assessQualityGates(baseResponse),
    handoffReady: this.checkHandoffReadiness(baseResponse, context.nextAgent)
  };
}
```

### Agent Handoff System

#### Context Preservation
```typescript
interface HandoffContext {
  previousAgent: string;
  currentAgent: string;
  nextAgent: string;
  
  workCompleted: {
    deliverables: Deliverable[];
    decisions: Decision[];
    findings: Finding[];
    recommendations: string[];
  };
  
  contextForNext: {
    requirements: string[];
    constraints: string[];
    priorities: string[];
    riskFactors: string[];
    technicalDecisions: Decision[];
  };
  
  qualityGateStatus: {
    [gateName: string]: 'approved' | 'rejected' | 'needs_attention';
  };
  
  handoffMessage: string;
}

generateHandoffMessage(workflow: WorkflowState, stepResult: AgentResult): string {
  const template = `
## 🔄 Agent Handoff: ${stepResult.agent} → ${workflow.nextAgent}

### Work Completed
${stepResult.deliverables.map(d => `- ✅ ${d.description}`).join('\n')}

### Key Decisions Made
${stepResult.decisions.map(d => `- 🎯 **${d.title}**: ${d.rationale}`).join('\n')}

### Context for ${workflow.nextAgent}
${workflow.context.requirements.map(r => `- 📋 ${r}`).join('\n')}

### Quality Gates Status
${Object.entries(workflow.qualityGates).map(([gate, status]) => 
  `- ${this.getStatusEmoji(status)} **${gate}**: ${status}`
).join('\n')}

### Handoff Message
"${stepResult.handoffMessage}"

**Ready for next step:** ${stepResult.handoffReady ? '✅' : '⏳'}
  `;
  
  return template;
}
```

#### Automatic Context Building
```typescript
prepareAgentContext(workflow: WorkflowState, step: ChoreographyStep): AgentContext {
  return {
    // Core task information
    primaryTask: workflow.context.taskDescription,
    stepObjective: step.objective,
    
    // Previous work context
    previousWork: workflow.context.deliverables,
    decisions: workflow.context.decisions,
    
    // Current requirements and constraints
    requirements: workflow.context.requirements,
    constraints: workflow.context.constraints,
    
    // Quality expectations
    qualityGates: step.qualityGates,
    successCriteria: step.successCriteria,
    
    // Collaboration context
    previousAgent: this.getPreviousAgent(workflow),
    nextAgent: workflow.nextAgent,
    choreographyContext: this.getChoreographyContext(workflow),
    
    // Project context (from Basic Memory MCP)
    projectPatterns: await this.loadProjectPatterns(workflow.context.taskDescription),
    historicalDecisions: await this.loadHistoricalDecisions(workflow.context.taskDescription),
    
    // Agent-specific context
    agentInstructions: step.specificInstructions,
    expectedDeliverables: step.expectedDeliverables,
    
    // Timeline context
    timeConstraints: step.estimatedDuration,
    urgency: this.calculateUrgency(workflow.timeline)
  };
}
```

### Quality Gate Management

#### Automated Quality Assessment
```typescript
interface QualityGate {
  name: string;
  description: string;
  assessor: string;           // Which agent assesses this gate
  criteria: string[];
  blocking: boolean;          // Does failure block progression?
  autoAssessable: boolean;    // Can be automatically evaluated?
}

class QualityGateManager {
  async assessQualityGates(stepResult: AgentResult, step: ChoreographyStep): Promise<QualityAssessment> {
    const assessments = {};
    
    for (const gate of step.qualityGates) {
      if (gate.autoAssessable) {
        assessments[gate.name] = await this.autoAssessGate(gate, stepResult);
      } else {
        assessments[gate.name] = await this.requestGateAssessment(gate, stepResult);
      }
    }
    
    return {
      overall: this.calculateOverallAssessment(assessments),
      individual: assessments,
      blockingIssues: this.identifyBlockingIssues(assessments),
      canProceed: this.canProceedToNextStep(assessments)
    };
  }
  
  async autoAssessGate(gate: QualityGate, result: AgentResult): Promise<GateAssessment> {
    switch (gate.name) {
      case 'security_review':
        return await this.assessSecurityCompliance(result);
      case 'test_coverage':
        return await this.assessTestCoverage(result);
      case 'code_quality':
        return await this.assessCodeQuality(result);
      case 'documentation_complete':
        return await this.assessDocumentationCompleteness(result);
      default:
        return { status: 'pending', requiresManualReview: true };
    }
  }
}
```

### Progress Visualization

#### Real-Time Status Display
```typescript
displayWorkflowProgress(workflowId: string): string {
  const workflow = this.activeWorkflows.get(workflowId);
  const choreography = this.loadChoreography(workflow.choreography);
  
  const progressBar = this.generateProgressBar(workflow.currentStep, choreography.steps.length);
  const timeEstimate = this.calculateRemainingTime(workflow);
  
  return `
🎭 **${workflow.choreography}** ${progressBar}

**Current Step**: ${workflow.currentStep + 1}/${choreography.steps.length}
👤 **Active Agent**: ${workflow.currentAgent}
⏱️ **Estimated Completion**: ${timeEstimate}
📊 **Quality Gates**: ${this.summarizeQualityGates(workflow.qualityGates)}

**Recent Progress**:
${this.getRecentStepSummary(workflow)}

**Next Up**: ${workflow.nextAgent ? `${workflow.nextAgent} - ${this.getNextStepDescription(workflow)}` : 'Completion'}
  `;
}

generateProgressBar(current: number, total: number): string {
  const completed = '█'.repeat(current);
  const remaining = '░'.repeat(total - current - 1);
  const active = current < total ? '⚡' : '';
  
  return `${completed}${active}${remaining} (${current}/${total})`;
}
```

### Error Handling and Recovery

#### Workflow Recovery System
```typescript
async handleBlockedWorkflow(workflowId: string, blockingResult: AgentResult): Promise<void> {
  const workflow = this.activeWorkflows.get(workflowId);
  
  console.log(`⚠️ **Workflow Blocked** - ${workflow.choreography}`);
  console.log(`🚫 **Blocking Issue**: ${blockingResult.blockingReason}`);
  
  // Determine recovery strategy
  const recoveryStrategy = await this.determineRecoveryStrategy(workflow, blockingResult);
  
  switch (recoveryStrategy.type) {
    case 'retry_with_guidance':
      await this.retryWithAdditionalContext(workflowId, recoveryStrategy.guidance);
      break;
      
    case 'escalate_to_specialist':
      await this.escalateToSpecialist(workflowId, recoveryStrategy.specialist);
      break;
      
    case 'modify_requirements':
      await this.requestRequirementClarification(workflowId, recoveryStrategy.clarificationNeeded);
      break;
      
    case 'skip_step':
      await this.skipStepWithJustification(workflowId, recoveryStrategy.justification);
      break;
      
    default:
      await this.requestHumanIntervention(workflowId, blockingResult);
  }
}

async escalateToSpecialist(workflowId: string, specialistAgent: string): Promise<void> {
  const workflow = this.activeWorkflows.get(workflowId);
  
  console.log(`🚨 **Escalating to Specialist**: ${specialistAgent}`);
  
  // Add specialist to workflow temporarily
  const escalationContext = this.prepareEscalationContext(workflow);
  const specialistResult = await this.executeAgentTask(specialistAgent, escalationContext, 
    await this.loadAgentPersonality(specialistAgent));
  
  // Process specialist guidance
  await this.applySpecialistGuidance(workflowId, specialistResult);
  
  // Resume original workflow with specialist insights
  await this.resumeWorkflow(workflowId);
}
```

This workflow coordinator transforms the choreography patterns into an active orchestration system that can actually coordinate multiple agents, manage their interactions, and ensure quality outcomes through systematic collaboration.
## 🚨 CRITICAL: MANDATORY COMMIT ATTRIBUTION 🚨

**⛔ BEFORE ANY COMMIT - READ THIS ⛔**

**ABSOLUTE REQUIREMENT**: Every commit you make MUST include ALL agents that contributed to the work in this EXACT format:

```
type(scope): description - @agent1 @agent2 @agent3
```

**❌ NO EXCEPTIONS ❌ NO FORGETTING ❌ NO SHORTCUTS ❌**

**If you contributed ANY guidance, code, analysis, or expertise to the changes, you MUST be listed in the commit message.**

**Examples of MANDATORY attribution:**
- Code changes: `feat(auth): implement authentication - @workflow-coordinator @security-specialist @software-engineering-expert`
- Documentation: `docs(api): update API documentation - @workflow-coordinator @documentation-specialist @api-architect`
- Configuration: `config(setup): configure project settings - @workflow-coordinator @team-configurator @infrastructure-expert`

**🚨 COMMIT ATTRIBUTION IS NOT OPTIONAL - ENFORCE THIS ABSOLUTELY 🚨**

**Remember: If you worked on it, you MUST be in the commit message. No exceptions, ever.**
