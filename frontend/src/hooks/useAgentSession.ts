"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { DocumentSessionState, TraceStep, AuditCheck } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const MOCK_DOCUMENT_CONTENT_1 = `# Product Requirements: DocuFlow AI Core

This document outlines the core agentic capabilities for the next-generation document orchestration platform. The objective is to transition from static templates to **dynamic agentic flows** that adapt to user intent in real-time.

### 1. Functional Objectives
* Automated discovery of document relationships across 256+ data types.
* Integration with "Aurora" state management for visual processing feedback.
* Multi-agent negotiation for conflicting compliance requirements.

> **AGENT NOTE**
> The "Compliance Check" module has been expanded to include Data Sovereignty protocols for EU-based nodes as per the latest session context.

### 2. Technical Constraints
| Attribute | Spec |
| --- | --- |
| Latency Target | < 150ms |
| Uptime SLA | 99.99% |
`;

const MOCK_DOCUMENT_CONTENT_2 = MOCK_DOCUMENT_CONTENT_1 + `
### 3. Rate Limiting & Token Buckets
* Token bucket algorithms implemented natively at gateway level.
* Support for backpressure indicators on active WS channels.
* Dynamic queuing for request throttling up to 10k concurrent sessions.
`;

export function useAgentSession(sessionId: string) {
  const [session, setSession] = useState<DocumentSessionState>({
    sessionId,
    archetype: "Technical",
    documentContent: "",
    status: "idle",
    loopCount: 0,
    maxLoops: 3,
    scorecard: {
      score: 0,
      checks: [
        { id: "sec", name: "Security Layer", status: "pending" },
        { id: "sov", name: "Data Sovereignty", status: "pending" },
        { id: "tok", name: "Token Handling", status: "pending" },
        { id: "rat", name: "Rate Limiting", status: "pending" },
      ],
      summary: "Draft validation pending.",
    },
    trace: [
      { id: "1", name: "Context Analysis", description: "System identified 14 technical constraints from legacy documentation.", status: "pending" },
      { id: "2", name: "Architecture Mapping", description: "Generated microservices topology for DocuFlow Core.", status: "pending" },
      { id: "3", name: "PRD Synthesis", description: "Assembling requirements into markdown structure...", status: "pending" },
      { id: "4", name: "Validation Check", description: "Pending draft finalization.", status: "pending" },
    ],
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSimulated, setIsSimulated] = useState(false);
  
  const simulationRef = useRef<number | null>(null);

  // Stop simulation on unmount
  useEffect(() => {
    return () => {
      if (simulationRef.current) clearInterval(simulationRef.current);
    };
  }, []);

  // Simulator helper function
  const runSimulation = useCallback((loop: number, feedback?: string) => {
    setIsGenerating(true);
    setIsSimulated(true);

    if (loop === 0) {
      // Step 1: Context Analysis
      setSession((prev) => ({
        ...prev,
        status: "running",
        trace: prev.trace.map((t, idx) => 
          idx === 0 ? { ...t, status: "active" } : t
        ),
      }));

      // Timeline of steps
      setTimeout(() => {
        // Complete step 1, start step 2
        setSession((prev) => ({
          ...prev,
          trace: prev.trace.map((t, idx) => {
            if (idx === 0) return { ...t, status: "completed" };
            if (idx === 1) return { ...t, status: "active" };
            return t;
          }),
        }));
      }, 1500);

      setTimeout(() => {
        // Complete step 2, start step 3 (PRD Synthesis)
        setSession((prev) => ({
          ...prev,
          trace: prev.trace.map((t, idx) => {
            if (idx === 1) return { ...t, status: "completed" };
            if (idx === 2) return { ...t, status: "active", progress: 0 };
            return t;
          }),
        }));

        // Stream text
        let charIndex = 0;
        const text = MOCK_DOCUMENT_CONTENT_1;
        const intervalTime = 15; // ms per chunk

        if (simulationRef.current) clearInterval(simulationRef.current);
        
        const intervalId = window.setInterval(() => {
          charIndex += 4;
          if (charIndex >= text.length) {
            clearInterval(intervalId);
            setIsGenerating(false);
            
            // Start Step 4: Validation Check (Critic Node)
            setSession((prev) => ({
              ...prev,
              documentContent: text,
              trace: prev.trace.map((t, idx) => {
                if (idx === 2) return { ...t, status: "completed", progress: 100 };
                if (idx === 3) return { ...t, status: "active" };
                return t;
              }),
            }));

            // Complete Critique validation
            setTimeout(() => {
              setSession((prev) => ({
                ...prev,
                status: "paused",
                scorecard: {
                  score: 88,
                  checks: [
                    { id: "sec", name: "Security Layer", status: "verified" },
                    { id: "sov", name: "Data Sovereignty", status: "verified" },
                    { id: "tok", name: "Token Handling", status: "attention" },
                    { id: "rat", name: "Rate Limiting", status: "pending" },
                  ],
                  summary: "Critic flagged missing Rate Limiting specs and ambiguous Token Handling protocols.",
                },
                trace: prev.trace.map((t, idx) => 
                  idx === 3 ? { ...t, status: "completed" } : t
                ),
              }));
            }, 2000);
          } else {
            setSession((prev) => ({
              ...prev,
              documentContent: text.substring(0, charIndex),
              trace: prev.trace.map((t, idx) => 
                idx === 2 ? { ...t, progress: Math.min(99, Math.floor((charIndex / text.length) * 100)) } : t
              ),
            }));
          }
        }, intervalTime);
        
        simulationRef.current = intervalId;
      }, 3000);
    } else {
      // Loop 1 (Revision request)
      setSession((prev) => ({
        ...prev,
        status: "running",
        loopCount: loop,
        trace: prev.trace.map((t, idx) => {
          if (idx === 2) return { ...t, status: "active", progress: 66, description: "Amending text based on user feedback..." };
          if (idx === 3) return { ...t, status: "pending" };
          return t;
        }),
      }));

      setTimeout(() => {
        // Stream the additional section
        let charIndex = MOCK_DOCUMENT_CONTENT_1.length;
        const text = MOCK_DOCUMENT_CONTENT_2;
        const intervalTime = 15;

        if (simulationRef.current) clearInterval(simulationRef.current);

        const intervalId = window.setInterval(() => {
          charIndex += 4;
          if (charIndex >= text.length) {
            clearInterval(intervalId);
            setIsGenerating(false);

            setSession((prev) => ({
              ...prev,
              documentContent: text,
              trace: prev.trace.map((t, idx) => {
                if (idx === 2) return { ...t, status: "completed", progress: 100, description: "Revision compilation completed." };
                if (idx === 3) return { ...t, status: "active", description: "Critic validating changes..." };
                return t;
              }),
            }));

            // Final Critic score check
            setTimeout(() => {
              setSession((prev) => ({
                ...prev,
                status: "paused", // Paused again for approval
                scorecard: {
                  score: 98,
                  checks: [
                    { id: "sec", name: "Security Layer", status: "verified" },
                    { id: "sov", name: "Data Sovereignty", status: "verified" },
                    { id: "tok", name: "Token Handling", status: "verified" },
                    { id: "rat", name: "Rate Limiting", status: "verified" },
                  ],
                  summary: "Critic check verified. Rate Limiting and Token Handling meet design requirements.",
                },
                trace: prev.trace.map((t, idx) => 
                  idx === 3 ? { ...t, status: "completed", description: "Audit checks successful." } : t
                ),
              }));
            }, 2000);
          } else {
            setSession((prev) => ({
              ...prev,
              documentContent: text.substring(0, charIndex),
            }));
          }
        }, intervalTime);

        simulationRef.current = intervalId;
      }, 1500);
    }
  }, []);

  // Main execution logic: Connects to SSE or starts simulation
  useEffect(() => {
    if (!sessionId) return;

    // Connect to actual SSE endpoint if available (check process.env or fallback)
    const apiEndpoint = `${API_BASE_URL}/api/documents/${sessionId}/stream`;
    
    // We try to test if backend exists, else we fall back to simulation
    const testAndConnect = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/documents/${sessionId}`, { method: "HEAD" });
        if (res.ok) {
          // Backend is running, connect to SSE EventSource
          const eventSource = new EventSource(apiEndpoint);
          
          eventSource.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data);
              setSession(data);
              if (data.status === "running") {
                setIsGenerating(true);
              } else {
                setIsGenerating(false);
              }
            } catch (err) {
              console.error("SSE parse error", err);
            }
          };

          eventSource.onerror = (err) => {
            console.error("SSE error", err);
            setError("SSE channel disconnected. Falling back to local offline simulation.");
            eventSource.close();
            // Start simulation as recovery
            runSimulation(0);
          };

          return () => eventSource.close();
        } else {
          // HTTP error, start mock simulation
          runSimulation(0);
        }
      } catch (e) {
        // Fetch failed (network error / backend not running), start mock simulation
        runSimulation(0);
      }
    };

    testAndConnect();
  }, [sessionId, runSimulation]);

  // Request a revision
  const requestRevision = useCallback(async (feedback: string) => {
    if (isSimulated) {
      runSimulation(session.loopCount + 1, feedback);
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/${sessionId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback }),
      });
      if (!res.ok) throw new Error("Feedback request failed.");
    } catch (err) {
      console.error(err);
      setError("Failed to send feedback to server. Simulating request instead.");
      runSimulation(session.loopCount + 1, feedback);
    }
  }, [sessionId, session.loopCount, isSimulated, runSimulation]);

  // Approve & Deploy
  const approve = useCallback(async () => {
    setSession((prev) => ({ ...prev, status: "running" }));
    setIsGenerating(true);

    if (isSimulated) {
      setTimeout(() => {
        setSession((prev) => ({
          ...prev,
          status: "completed",
        }));
        setIsGenerating(false);
      }, 2000);
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/${sessionId}/approve`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Approval submission failed.");
    } catch (err) {
      console.error(err);
      setError("Failed to approve document on server. Simulating approval completion.");
      setTimeout(() => {
        setSession((prev) => ({
          ...prev,
          status: "completed",
        }));
        setIsGenerating(false);
      }, 2000);
    }
  }, [sessionId, isSimulated]);

  return {
    session,
    isGenerating,
    error,
    requestRevision,
    approve,
  };
}
