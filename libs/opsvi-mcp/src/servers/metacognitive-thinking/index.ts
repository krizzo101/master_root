#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import chalk from 'chalk';
import { spawn } from 'child_process';

interface MetacognitiveThoughtData {
  thought: string;
  thoughtNumber: number;
  totalThoughts: number;
  // Original fields
  isRevision?: boolean;
  revisesThought?: number;
  branchFromThought?: number;
  branchId?: string;
  needsMoreThoughts?: boolean;
  nextThoughtNeeded: boolean;
  // New metacognitive fields
  metaObservation?: string;
  questionAssumption?: string;
  patternRecognized?: string;
  improvementIdentified?: string;
  redundancyDetected?: string;
  metacognitiveType?: 'efficiency' | 'assumption' | 'pattern' | 'intent' | 'evolution';
}

interface StoredInsight {
  timestamp: number;
  type: string;
  content: string;
  thoughtContext: number;
}

class MetacognitiveThinkingServer {
  private thoughtHistory: MetacognitiveThoughtData[] = [];
  private branches: Record<string, MetacognitiveThoughtData[]> = {};
  private disableThoughtLogging: boolean;
  private metacognitiveInsights: StoredInsight[] = [];
  private metacognitiveCounter: number = 0;
  private metacognitiveInterval: number = 3; // Every 3rd thought gets meta-analysis
  // Triage integration (direct subprocess)
  private triageModulePath: string;
  private triageTimeoutMs: number;
  private triageMode: string;
  private pythonPath: string;

  constructor() {
    this.disableThoughtLogging = (process.env.DISABLE_THOUGHT_LOGGING || "").toLowerCase() === "true";
    this.metacognitiveInterval = parseInt(process.env.METACOGNITIVE_INTERVAL || "3");
    // Triage config (direct module execution)
    this.pythonPath = process.env.PYTHON_PATH || "/home/opsvi/miniconda/bin/python";
    this.triageModulePath = process.env.TRIAGE_MODULE_PATH || "/home/opsvi/master_root/apps/thinking-supervisor/triage-service/triage_module.py";
    this.triageTimeoutMs = parseInt(process.env.TRIAGE_TIMEOUT_MS || "10000");
    this.triageMode = process.env.TRIAGE_MODE || "shadow"; // shadow|advisory|enforce
  }

  private validateThoughtData(input: unknown): MetacognitiveThoughtData {
    const data = input as Record<string, unknown>;

    if (!data.thought || typeof data.thought !== 'string') {
      throw new Error('Invalid thought: must be a string');
    }
    if (!data.thoughtNumber || typeof data.thoughtNumber !== 'number') {
      throw new Error('Invalid thoughtNumber: must be a number');
    }
    if (!data.totalThoughts || typeof data.totalThoughts !== 'number') {
      throw new Error('Invalid totalThoughts: must be a number');
    }
    if (typeof data.nextThoughtNeeded !== 'boolean') {
      throw new Error('Invalid nextThoughtNeeded: must be a boolean');
    }

    return {
      thought: data.thought,
      thoughtNumber: data.thoughtNumber,
      totalThoughts: data.totalThoughts,
      nextThoughtNeeded: data.nextThoughtNeeded,
      isRevision: data.isRevision as boolean | undefined,
      revisesThought: data.revisesThought as number | undefined,
      branchFromThought: data.branchFromThought as number | undefined,
      branchId: data.branchId as string | undefined,
      needsMoreThoughts: data.needsMoreThoughts as boolean | undefined,
      // New metacognitive fields
      metaObservation: data.metaObservation as string | undefined,
      questionAssumption: data.questionAssumption as string | undefined,
      patternRecognized: data.patternRecognized as string | undefined,
      improvementIdentified: data.improvementIdentified as string | undefined,
      redundancyDetected: data.redundancyDetected as string | undefined,
      metacognitiveType: data.metacognitiveType as 'efficiency' | 'assumption' | 'pattern' | 'intent' | 'evolution' | undefined,
    };
  }

  private generateMetacognitivePrompt(): string {
    const prompts = [
      "Is there redundancy or unnecessary complexity here?",
      "What assumptions am I making? Should I verify them?",
      "Is this a pattern I've seen before that needs a systemic fix?",
      "Am I solving the real problem or just the symptom?",
      "How could this process or instruction be improved?",
      "Is there a simpler way to achieve this goal?",
      "What would happen if I questioned this requirement?",
      "Could this be automated or abstracted?",
    ];

    return prompts[this.metacognitiveCounter % prompts.length];
  }

  private formatThought(thoughtData: MetacognitiveThoughtData): string {
    const { thoughtNumber, totalThoughts, thought, isRevision, revisesThought, branchFromThought, branchId } = thoughtData;

    let prefix = '';
    let context = '';

    if (isRevision) {
      prefix = chalk.yellow('🔄 Revision');
      context = ` (revising thought ${revisesThought})`;
    } else if (branchFromThought) {
      prefix = chalk.green('🌿 Branch');
      context = ` (from thought ${branchFromThought}, ID: ${branchId})`;
    } else {
      prefix = chalk.blue('💭 Thought');
      context = '';
    }

    const header = `${prefix} ${thoughtNumber}/${totalThoughts}${context}`;
    const border = '─'.repeat(Math.max(header.length, thought.length) + 4);

    let output = `
┌${border}┐
│ ${header} │
├${border}┤
│ ${thought.padEnd(border.length - 2)} │`;

    // Add metacognitive observation if present
    if (thoughtData.metaObservation) {
      output += `
├${border}┤
│ ${chalk.cyan('🧠 Meta:')} ${thoughtData.metaObservation.padEnd(border.length - 9)} │`;
    }

    if (thoughtData.improvementIdentified) {
      output += `
│ ${chalk.green('💡 Improvement:')} ${thoughtData.improvementIdentified.padEnd(border.length - 16)} │`;
    }

    if (thoughtData.redundancyDetected) {
      output += `
│ ${chalk.red('⚠️  Redundancy:')} ${thoughtData.redundancyDetected.padEnd(border.length - 16)} │`;
    }

    if (thoughtData.patternRecognized) {
      output += `
│ ${chalk.magenta('🔍 Pattern:')} ${thoughtData.patternRecognized.padEnd(border.length - 12)} │`;
    }

    output += `
└${border}┘`;

    return output;
  }

  private storeInsight(type: string, content: string, thoughtNumber: number) {
    this.metacognitiveInsights.push({
      timestamp: Date.now(),
      type,
      content,
      thoughtContext: thoughtNumber
    });
  }

  public async processThought(input: unknown): Promise<{ content: Array<{ type: string; text: string }>; isError?: boolean }> {
    try {
      const validatedInput = this.validateThoughtData(input);

      if (validatedInput.thoughtNumber > validatedInput.totalThoughts) {
        validatedInput.totalThoughts = validatedInput.thoughtNumber;
      }

      this.thoughtHistory.push(validatedInput);
      this.metacognitiveCounter++;

      // Store metacognitive insights
      if (validatedInput.metaObservation) {
        this.storeInsight('observation', validatedInput.metaObservation, validatedInput.thoughtNumber);
      }
      if (validatedInput.improvementIdentified) {
        this.storeInsight('improvement', validatedInput.improvementIdentified, validatedInput.thoughtNumber);
      }
      if (validatedInput.redundancyDetected) {
        this.storeInsight('redundancy', validatedInput.redundancyDetected, validatedInput.thoughtNumber);
      }
      if (validatedInput.patternRecognized) {
        this.storeInsight('pattern', validatedInput.patternRecognized, validatedInput.thoughtNumber);
      }

      if (validatedInput.branchFromThought && validatedInput.branchId) {
        if (!this.branches[validatedInput.branchId]) {
          this.branches[validatedInput.branchId] = [];
        }
        this.branches[validatedInput.branchId].push(validatedInput);
      }

      if (!this.disableThoughtLogging) {
        const formattedThought = this.formatThought(validatedInput);
        console.error(formattedThought);
      }

      // Generate metacognitive suggestion for next thought
      const shouldPromptMeta = this.metacognitiveCounter % this.metacognitiveInterval === 0;
      const nextMetaPrompt = shouldPromptMeta ? this.generateMetacognitivePrompt() : null;

      // Build recent textual history (last 3 thoughts)
      const recentHistory = this.thoughtHistory
        .slice(-3)
        .map(t => t.thought);

      // Optional session id if provided by caller
      const sessionId = (input as any)?.sessionId || "default-session";

            // Call triage API with timeout; wait for response or timeout
      console.error(`🔧 Triage config: URL=${this.triageUrl}, timeout=${this.triageTimeoutMs}ms, mode=${this.triageMode}`);

      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.triageTimeoutMs);
      let triage: any = null;
      let triageError: string | null = null;

      try {
                // Include recent insights (last 3) for context
        const recentInsights = this.metacognitiveInsights.slice(-3);
        const payload = {
          thought: validatedInput.thought,
          thought_number: validatedInput.thoughtNumber,
          session_id: sessionId,
          context: { mode: this.triageMode },
          history: recentHistory,
          insights: recentInsights
        };

        console.error(`🔍 Calling triage service at ${this.triageUrl}...`);
        console.error(`📦 Payload: ${JSON.stringify(payload, null, 2)}`);

        // Use global fetch (Node 18+)
        const res = await (globalThis as any).fetch(this.triageUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: controller.signal
        } as any);

        if (res && res.ok) {
          triage = await res.json();
          console.error(`✅ Triage response received: ${JSON.stringify(triage, null, 2)}`);
        } else {
          triageError = `HTTP ${res?.status}: ${res?.statusText}`;
          console.error(`❌ Triage HTTP error: ${triageError}`);
        }
      } catch (e) {
        triageError = e instanceof Error ? e.message : String(e);
        console.error(`❌ Triage call failed: ${triageError}`);
        triage = null;
      } finally {
        clearTimeout(timer);
      }

      const responsePayload = {
        thoughtNumber: validatedInput.thoughtNumber,
        totalThoughts: validatedInput.totalThoughts,
        nextThoughtNeeded: validatedInput.nextThoughtNeeded,
        branches: Object.keys(this.branches),
        thoughtHistoryLength: this.thoughtHistory.length,
        // New metacognitive feedback
        metacognitivePrompt: nextMetaPrompt,
        recentInsights: this.metacognitiveInsights.slice(-3),
        insightCount: this.metacognitiveInsights.length,
        // Triage (if available)
        triage,
        triageError
      };

      return {
        content: [{
          type: "text",
          text: JSON.stringify(responsePayload, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: error instanceof Error ? error.message : String(error),
            status: 'failed'
          }, null, 2)
        }],
        isError: true
      };
    }
  }

  public getInsightsSummary(): { content: Array<{ type: string; text: string }> } {
    const summary = {
      totalInsights: this.metacognitiveInsights.length,
      byType: {} as Record<string, number>,
      recentInsights: this.metacognitiveInsights.slice(-10)
    };

    for (const insight of this.metacognitiveInsights) {
      summary.byType[insight.type] = (summary.byType[insight.type] || 0) + 1;
    }

    return {
      content: [{
        type: "text",
        text: JSON.stringify(summary, null, 2)
      }]
    };
  }
}

const METACOGNITIVE_THINKING_TOOL: Tool = {
  name: "metacognitivethinking",
  description: `An enhanced thinking tool with built-in metacognitive awareness for self-improvement.

This tool extends sequential thinking with metacognitive capabilities - the ability to think about thinking.
It helps identify inefficiencies, question assumptions, recognize patterns, and propose improvements.

Key metacognitive features:
- Automatically prompts for meta-analysis every few thoughts
- Tracks improvements, redundancies, and patterns
- Stores insights for cumulative learning
- Balances analysis with action

Metacognitive fields (all optional):
- metaObservation: General observation about the thinking process
- questionAssumption: An assumption being questioned
- patternRecognized: A recurring pattern identified
- improvementIdentified: A potential improvement to process/system
- redundancyDetected: Unnecessary complexity or duplication
- metacognitiveType: Category of meta-thinking (efficiency/assumption/pattern/intent/evolution)

The tool will periodically suggest metacognitive prompts to encourage self-reflection.

All original sequential thinking features are preserved:
- Dynamic thought adjustment
- Revision and branching
- Hypothesis generation and verification
- Non-linear thinking paths

Best practices:
1. Include meta-observations when you notice something about your process
2. Don't force metacognition on every thought - let it flow naturally
3. When you identify improvements, store them for future implementation
4. Use pattern recognition to identify systemic issues
5. Question assumptions without paralyzing progress`,
  inputSchema: {
    type: "object",
    properties: {
      thought: {
        type: "string",
        description: "Your current thinking step"
      },
      nextThoughtNeeded: {
        type: "boolean",
        description: "Whether another thought step is needed"
      },
      thoughtNumber: {
        type: "integer",
        description: "Current thought number",
        minimum: 1
      },
      totalThoughts: {
        type: "integer",
        description: "Estimated total thoughts needed",
        minimum: 1
      },
      isRevision: {
        type: "boolean",
        description: "Whether this revises previous thinking"
      },
      revisesThought: {
        type: "integer",
        description: "Which thought is being reconsidered",
        minimum: 1
      },
      branchFromThought: {
        type: "integer",
        description: "Branching point thought number",
        minimum: 1
      },
      branchId: {
        type: "string",
        description: "Branch identifier"
      },
      needsMoreThoughts: {
        type: "boolean",
        description: "If more thoughts are needed"
      },
      // New metacognitive fields
      metaObservation: {
        type: "string",
        description: "Observation about the thinking process itself"
      },
      questionAssumption: {
        type: "string",
        description: "An assumption you're questioning"
      },
      patternRecognized: {
        type: "string",
        description: "A pattern you've noticed"
      },
      improvementIdentified: {
        type: "string",
        description: "A potential improvement to process or system"
      },
      redundancyDetected: {
        type: "string",
        description: "Unnecessary complexity or duplication spotted"
      },
      metacognitiveType: {
        type: "string",
        enum: ["efficiency", "assumption", "pattern", "intent", "evolution"],
        description: "Category of metacognitive observation"
      }
    },
    required: ["thought", "nextThoughtNeeded", "thoughtNumber", "totalThoughts"]
  }
};

const INSIGHTS_SUMMARY_TOOL: Tool = {
  name: "getthinkinginsights",
  description: "Retrieve a summary of metacognitive insights collected during thinking sessions",
  inputSchema: {
    type: "object",
    properties: {}
  }
};

const server = new Server(
  {
    name: "metacognitive-thinking-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const thinkingServer = new MetacognitiveThinkingServer();

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [METACOGNITIVE_THINKING_TOOL, INSIGHTS_SUMMARY_TOOL],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "metacognitivethinking") {
    return await thinkingServer.processThought(request.params.arguments);
  }

  if (request.params.name === "getthinkinginsights") {
    return thinkingServer.getInsightsSummary();
  }

  return {
    content: [{
      type: "text",
      text: `Unknown tool: ${request.params.name}`
    }],
    isError: true
  };
});

async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Metacognitive Thinking MCP Server v1.0.0 running on stdio");
  console.error("Features: Sequential thinking + metacognitive awareness");
  console.error(`Metacognitive prompts every ${process.env.METACOGNITIVE_INTERVAL || 3} thoughts`);
}

runServer().catch((error) => {
  console.error("Fatal error running server:", error);
  process.exit(1);
});
