/**
 * Triage Client for MCP Thinking Server Integration
 * Connects to Python triage service for thought analysis
 */

interface ThoughtAnalysis {
  thought: string;
  thought_number: number;
  session_id: string;
  context?: Record<string, any>;
  history?: string[];
}

interface TriageResponse {
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  should_escalate: boolean;
  confidence: number;
  reasoning?: string;
  intervention?: Record<string, any>;
  collected_data: Record<string, any>;
}

export class ThinkingTriageClient {
  private triageUrl: string;
  private enabled: boolean;
  private mode: 'shadow' | 'advisory' | 'enforcement';
  private sessionId: string;
  private thoughtHistory: string[] = [];
  private thoughtCount: number = 0;

  constructor() {
    // Configuration from environment
    this.triageUrl = process.env.TRIAGE_SERVICE_URL || 'http://localhost:8100';
    this.enabled = process.env.TRIAGE_ENABLED === 'true';
    this.mode = (process.env.TRIAGE_MODE as any) || 'shadow';
    this.sessionId = `mcp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    if (this.enabled) {
      console.log(`[Triage] Enabled in ${this.mode} mode`);
    }
  }

  /**
   * Process a thought through triage
   * Returns null in shadow mode, intervention in other modes
   */
  async processThought(thought: string, context?: Record<string, any>): Promise<TriageResponse | null> {
    if (!this.enabled) {
      return null;
    }

    this.thoughtCount++;
    this.thoughtHistory.push(thought);

    // Keep history limited to last 10 thoughts
    if (this.thoughtHistory.length > 10) {
      this.thoughtHistory.shift();
    }

    const analysis: ThoughtAnalysis = {
      thought,
      thought_number: this.thoughtCount,
      session_id: this.sessionId,
      context: context || {},
      history: this.thoughtHistory.slice(-5) // Last 5 thoughts for context
    };

    try {
      const response = await fetch(`${this.triageUrl}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(analysis),
      });

      if (!response.ok) {
        console.error(`[Triage] API error: ${response.status}`);
        return null;
      }

      const result: TriageResponse = await response.json();

      // Log in shadow mode for debugging
      if (this.mode === 'shadow') {
        console.log(`[Triage Shadow] Risk: ${result.risk_level}, Would escalate: ${result.collected_data.would_have_escalated}`);
        return null; // Don't intervene in shadow mode
      }

      // In advisory/enforcement modes, return the intervention
      if (result.should_escalate) {
        console.log(`[Triage] Escalation triggered: ${result.reasoning}`);
        return result;
      }

      return null;
    } catch (error) {
      console.error(`[Triage] Failed to analyze thought:`, error);
      return null; // Fail open - don't block on errors
    }
  }

  /**
   * Get metrics from the triage service
   */
  async getMetrics(): Promise<any> {
    if (!this.enabled) {
      return null;
    }

    try {
      const response = await fetch(`${this.triageUrl}/metrics`);
      return await response.json();
    } catch (error) {
      console.error(`[Triage] Failed to get metrics:`, error);
      return null;
    }
  }

  /**
   * Reset session (for new conversation)
   */
  resetSession(): void {
    this.sessionId = `mcp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.thoughtHistory = [];
    this.thoughtCount = 0;
  }
}

// Integration hook for existing MCP thinking server
export function enhanceThinkingServer(originalProcess: Function): Function {
  const triageClient = new ThinkingTriageClient();

  return async function enhancedProcess(params: any): Promise<any> {
    // Get original response
    const response = await originalProcess(params);

    // Process through triage if we have a thought
    if (params.thought) {
      const intervention = await triageClient.processThought(
        params.thought,
        { needsMoreThoughts: params.nextThoughtNeeded }
      );

      // In enforcement mode, modify response
      if (intervention && intervention.should_escalate) {
        response.blocked = true;
        response.blockReason = intervention.reasoning;
        response.requirements = intervention.intervention;

        // Force user to address the issue
        response.nextThoughtNeeded = true;
        response.metacognitivePrompt = intervention.intervention?.prompt ||
          "The triage system has detected an issue with your thinking. Please address it.";
      }
    }

    return response;
  };
}
