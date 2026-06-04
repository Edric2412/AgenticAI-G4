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
  // Ref to hold the active EventSource so we can close/reopen it
  const eventSourceRef = useRef<EventSource | null>(null);
  const hasReceivedDataRef = useRef(false);
  const lastStatusRef = useRef<string | null>(null);

  useEffect(() => {
    return () => {
      if (simulationRef.current) clearInterval(simulationRef.current);
      if (eventSourceRef.current) eventSourceRef.current.close();
    };
  }, []);

  const runSimulation = useCallback((loop: number, feedback?: string) => {
    setIsGenerating(true);
    setIsSimulated(true);

    if (loop === 0) {
      setSession((prev) => ({
        ...prev,
        status: "running",
        trace: prev.trace.map((t, idx) =>
          idx === 0 ? { ...t, status: "active" } : t
        ),
      }));

      setTimeout(() => {
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
        setSession((prev) => ({
          ...prev,
          trace: prev.trace.map((t, idx) => {
            if (idx === 1) return { ...t, status: "completed" };
            if (idx === 2) return { ...t, status: "active", progress: 0 };
            return t;
          }),
        }));

        let charIndex = 0;
        const text = MOCK_DOCUMENT_CONTENT_1;
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
                if (idx === 2) return { ...t, status: "completed", progress: 100 };
                if (idx === 3) return { ...t, status: "active" };
                return t;
              }),
            }));
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
        }, 15);

        simulationRef.current = intervalId;
      }, 3000);
    } else {
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
        let charIndex = MOCK_DOCUMENT_CONTENT_1.length;
        const text = MOCK_DOCUMENT_CONTENT_2;
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
            setTimeout(() => {
              setSession((prev) => ({
                ...prev,
                status: "paused",
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
        }, 15);

        simulationRef.current = intervalId;
      }, 1500);
    }
  }, []);

  // ── Core SSE connection function ──────────────────────────────────────
  // Extracted as useCallback so requestRevision and approve can re-call it
  const connectToSSE = useCallback(() => {
    // Close any existing connection first
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    hasReceivedDataRef.current = false;
    lastStatusRef.current = null;

    const eventSource = new EventSource(
      `${API_BASE_URL}/api/documents/${sessionId}/stream`
    );
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setSession(data);
        setIsGenerating(data.status === "running");
        hasReceivedDataRef.current = true;
        lastStatusRef.current = data.status;
      } catch (err) {
        console.error("SSE parse error", err);
      }
    };

    eventSource.onerror = (err) => {
      // If we already received data and the last status is paused/completed,
      // the server closed the connection normally. Do not log an error or fallback to simulation.
      if (hasReceivedDataRef.current && (lastStatusRef.current === "paused" || lastStatusRef.current === "completed")) {
        eventSource.close();
        eventSourceRef.current = null;
        setIsGenerating(false);
        return;
      }

      console.error("SSE error", err);
      eventSource.close();
      eventSourceRef.current = null;

      // Only fall back to simulation if no real content was received
      if (hasReceivedDataRef.current) {
        setIsGenerating(false);
      } else {
        setError("SSE channel disconnected. Falling back to local offline simulation.");
        runSimulation(0);
      }
    };
  }, [sessionId, runSimulation]);

  // ── Initial connection on mount ───────────────────────────────────────
  useEffect(() => {
    if (!sessionId) return;

    const testAndConnect = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/documents/${sessionId}`, {
          method: "HEAD",
        });
        if (res.ok) {
          connectToSSE();
        } else {
          runSimulation(0);
        }
      } catch (e) {
        console.error("Backend unavailable, using simulation:", e);
        runSimulation(0);
      }
    };

    testAndConnect();
  }, [sessionId, connectToSSE, runSimulation]);

  // ── Request Revision ──────────────────────────────────────────────────
  const requestRevision = useCallback(async (feedback: string) => {
    if (isSimulated) {
      runSimulation(session.loopCount + 1, feedback);
      return;
    }

    try {
      setIsGenerating(true);
      setSession((prev) => ({ ...prev, status: "running" }));

      const res = await fetch(
        `${API_BASE_URL}/api/documents/${sessionId}/feedback`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ feedback }),
        }
      );
      if (!res.ok) throw new Error("Feedback request failed.");

      // ← KEY FIX: reconnect SSE to receive the revised document
      connectToSSE();
    } catch (err) {
      console.error(err);
      setError("Failed to send feedback. Simulating instead.");
      runSimulation(session.loopCount + 1, feedback);
    }
  }, [sessionId, session.loopCount, isSimulated, runSimulation, connectToSSE]);

  // ── Approve & Deploy ──────────────────────────────────────────────────
  const approve = useCallback(async () => {
    setSession((prev) => ({ ...prev, status: "running" }));
    setIsGenerating(true);

    if (isSimulated) {
      setTimeout(() => {
        setSession((prev) => ({ ...prev, status: "completed" }));
        setIsGenerating(false);
      }, 2000);
      return;
    }

    try {
      const res = await fetch(
        `${API_BASE_URL}/api/documents/${sessionId}/approve`,
        { method: "POST" }
      );
      if (!res.ok) throw new Error("Approval failed.");

      // ← KEY FIX: reconnect SSE to receive the completed status
      connectToSSE();
    } catch (err) {
      console.error(err);
      setError("Approval failed on server. Simulating completion.");
      setTimeout(() => {
        setSession((prev) => ({ ...prev, status: "completed" }));
        setIsGenerating(false);
      }, 2000);
    }
  }, [sessionId, isSimulated, connectToSSE]);

  return {
    session,
    isGenerating,
    error,
    requestRevision,
    approve,
  };
}