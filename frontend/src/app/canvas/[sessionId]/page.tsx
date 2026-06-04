"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Topbar from "@/components/Topbar";
import { useAgentSession } from "@/hooks/useAgentSession";

export default function AgenticCanvas() {
  const params = useParams();
  const sessionId = (params?.sessionId as string) || "";
  const { session, isGenerating, error, requestRevision, approve } = useAgentSession(sessionId);
  
  const [feedback, setFeedback] = useState("");
  const [copied, setCopied] = useState(false);
  const documentEndRef = useRef<HTMLDivElement | null>(null);

  // Typewriter effect state and refs
  const [displayedContent, setDisplayedContent] = useState("");
  const typingTimerRef = useRef<number | null>(null);
  const isInitialLoadRef = useRef(true);
  const lastLoopCountRef = useRef<number>(0);

  // Typewriter effect runner
  useEffect(() => {
    const targetContent = session?.documentContent || "";
    const currentLoopCount = session?.loopCount || 0;

    // Reset typewriter if we advance to a new loop (revision cycle)
    if (currentLoopCount !== lastLoopCountRef.current) {
      lastLoopCountRef.current = currentLoopCount;
      setDisplayedContent("");
      return;
    }

    if (typingTimerRef.current) {
      window.clearInterval(typingTimerRef.current);
      typingTimerRef.current = null;
    }

    if (!targetContent) {
      setDisplayedContent("");
      return;
    }

    // Show immediately if it's the initial page load with pre-existing content
    if (isInitialLoadRef.current) {
      const status = session?.status;
      if (status === "paused" || status === "completed") {
        setDisplayedContent(targetContent);
        isInitialLoadRef.current = false;
        return;
      } else {
        // It's actively generating (status is "running"), so type it out!
        isInitialLoadRef.current = false;
      }
    }

    if (targetContent.length <= displayedContent.length) {
      setDisplayedContent(targetContent);
      return;
    }

    // Increment character chunk per tick (faster for long documents)
    const step = Math.max(8, Math.ceil((targetContent.length - displayedContent.length) / 70));
    let currentLength = displayedContent.length;

    typingTimerRef.current = window.setInterval(() => {
      currentLength += step;
      if (currentLength >= targetContent.length) {
        setDisplayedContent(targetContent);
        if (typingTimerRef.current) {
          window.clearInterval(typingTimerRef.current);
          typingTimerRef.current = null;
        }
      } else {
        setDisplayedContent(targetContent.slice(0, currentLength));
      }
    }, 15);

    return () => {
      if (typingTimerRef.current) {
        window.clearInterval(typingTimerRef.current);
      }
    };
  }, [session?.documentContent, session?.loopCount]);

  // Auto-scroll document preview to bottom while generating content
  useEffect(() => {
    if (isGenerating && documentEndRef.current) {
      documentEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [displayedContent, isGenerating]);

  // Handle revision submit
  const handleRequestRevision = () => {
    if (!feedback.trim()) return;
    requestRevision(feedback);
    setFeedback("");
  };

  const handleApprove = () => {
    approve();
  };

  const handleCopy = () => {
    if (!session?.documentContent) return;
    navigator.clipboard.writeText(session.documentContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!session?.documentContent) return;
    const blob = new Blob([session.documentContent], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const filename = `${session.archetype || "Document"}_${sessionId}.md`;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const displaySessionId = sessionId ? sessionId.toUpperCase() : "SESSION";

  return (
    <main className="flex-1 flex flex-col relative overflow-hidden h-screen bg-surface text-on-surface ml-64 pt-16">
      {/* Background Glows */}
      <div className="aurora-glow">
        <div className="aurora-blob bg-primary/10 top-0 left-1/4"></div>
        <div className="aurora-blob bg-secondary/10 bottom-0 right-1/4" style={{ animationDelay: "-3s" }}></div>
      </div>

      {/* Top Bar */}
      <Topbar>
        <div className="flex items-center gap-4">
          <span className="font-display text-headline-lg text-lg text-on-surface">
            Agentic Canvas: {displaySessionId}
          </span>
          <span className="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant text-[10px] font-sans uppercase tracking-widest border border-outline-variant">
            {session?.status === "running" ? "Agent Generation Active" : `${(session?.status || "").toUpperCase()} SESSION`}
          </span>
        </div>
        <div className="flex items-center gap-4">
          {(session?.loopCount ?? 0) > 0 && (
            <div className="px-3 py-1 rounded bg-white/5 border border-white/10 text-xs font-mono text-tertiary">
              Self-Correction Loop: {session?.loopCount} / {session?.maxLoops}
            </div>
          )}
          <div className="flex -space-x-2">
            <img
              alt="User Avatar"
              className="w-8 h-8 rounded-full border-2 border-surface shadow-md"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuC4biUgCGM4lJkMoOxJQNud3NhJ7YMt1kPfV-JxPzW-3Hz_isJv7vb__gzESFP1w7_m7GWxN3OCAGeDa9VLuhEiGL2elfXAwF3oh-aBCxiJeM24xCANJCDrM80kME8J8B0k60Jg_dl4j3DVrOkUHEopI-bUEOl829auTxeFHdX8Sa7ySa0PoY5x96VZikn94aNddAvmAbr1xIjkjhRDEws6qgrJDZoM8kRF9I8UT6G5cSkU40escyQaxhwMsVywOy_o8l1-_3wN_sg"
            />
            <div className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container text-xs font-bold border-2 border-surface">
              AI
            </div>
          </div>
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-primary hover:bg-white/5 transition-colors p-2 rounded-full">
            notifications
          </span>
        </div>
      </Topbar>

      {/* Network Alert (Error message) */}
      {error && (
        <div className="bg-error/10 border-b border-error/20 px-6 py-2 flex items-center gap-2 text-error text-xs font-sans">
          <span className="material-symbols-outlined text-[16px]">warning</span>
          <span>{error}</span>
        </div>
      )}

      {/* 3-Column Workspace */}
      <div className="flex-1 flex overflow-hidden p-6 gap-6 pb-28">
        
        {/* Column 1: Execution Trace */}
        <section className="w-1/4 flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar">
          <h2 className="font-sans text-label-sm text-on-surface-variant flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">terminal</span> EXECUTION TRACE
          </h2>
          <div className="relative flex flex-col gap-6 pl-4 mt-2">
            {/* Connecting Circuit Line */}
            <div className="circuit-line left-[7px] top-4 bottom-4"></div>
            
            {session?.trace?.map((step, idx) => {
              const isCompleted = step.status === "completed";
              const isActive = step.status === "active";
              
              return (
                <div key={step.id} className={`relative z-10 flex gap-4 group transition-opacity duration-300 ${!isCompleted && !isActive ? "opacity-50" : ""}`}>
                  {/* Step Pip Indicators */}
                  {isCompleted ? (
                    <div className="w-4 h-4 rounded-full bg-outline flex-shrink-0 mt-1 shadow-[0_0_10px_rgba(140,144,159,0.5)]"></div>
                  ) : isActive ? (
                    <div className="w-4 h-4 rounded-full border-2 border-primary bg-surface flex-shrink-0 mt-1 animate-pulse shadow-[0_0_8px_rgba(173,198,255,0.6)]"></div>
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-outline-variant bg-surface flex-shrink-0 mt-1"></div>
                  )}

                  {/* Step details */}
                  <div className="flex flex-col gap-1 flex-1">
                    <span className={`font-sans text-sm font-semibold ${isActive ? "text-primary" : "text-on-surface"}`}>
                      {step.name}
                    </span>
                    <p className="text-xs text-on-surface-variant leading-relaxed font-body">
                      {step.description}
                    </p>
                    
                    {/* Render active progress bar if step is drafting */}
                    {isActive && step.progress !== undefined && (
                      <div className="w-full bg-surface-container h-1 rounded-full mt-2 overflow-hidden border border-outline-variant">
                        <div
                          className="bg-primary h-full transition-all duration-300 shadow-[0_0_8px_rgba(173,198,255,0.6)]"
                          style={{ width: `${step.progress}%` }}
                        ></div>
                      </div>
                    )}
                    
                    {isCompleted && (
                      <span className="text-[10px] font-sans text-outline uppercase tracking-wider mt-1">
                        Completed
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Column 2: Document Preview Canvas */}
        <section className="flex-1 bezel-card flex flex-col overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-outline-variant bg-surface-container-high shrink-0">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-outline-variant"></div>
              <div className="w-3 h-3 rounded-full bg-outline-variant"></div>
              <div className="w-3 h-3 rounded-full bg-outline-variant"></div>
            </div>
            <div className="flex items-center gap-4 text-xs font-sans text-on-surface-variant">
              <span className="cursor-default">UTF-8</span>
              <span className="cursor-default">Markdown</span>
              {session?.documentContent && (
                <>
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1 hover:text-primary transition-colors cursor-pointer"
                    title="Copy Raw Markdown"
                  >
                    <span className="material-symbols-outlined text-sm">
                      {copied ? "check" : "content_copy"}
                    </span>
                    <span>{copied ? "Copied" : "Copy"}</span>
                  </button>
                  <button
                    onClick={handleDownload}
                    className="flex items-center gap-1 hover:text-primary transition-colors cursor-pointer"
                    title="Download Markdown File"
                  >
                    <span className="material-symbols-outlined text-sm">download</span>
                    <span>Download</span>
                  </button>
                </>
              )}
              <span className="material-symbols-outlined text-sm cursor-pointer hover:text-primary transition-colors" title="Toggle Fullscreen">
                fullscreen
              </span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-12 bg-surface/30 custom-scrollbar">
            {displayedContent ? (
              <article className="max-w-2xl mx-auto space-y-6 font-body text-on-surface/90 leading-relaxed">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <div className="space-y-4 pb-2 border-b border-white/5">
                        <span className="text-primary font-sans text-label-sm tracking-widest uppercase">
                          Draft (Loop {session?.loopCount})
                        </span>
                        <h1 className="font-display text-4xl text-on-surface font-bold">
                          {children}
                        </h1>
                      </div>
                    ),
                    h3: ({ children }) => (
                      <h3 className="font-display text-xl text-primary flex items-center gap-2 pt-6 font-semibold">
                        <span className="w-2 h-2 rounded-full bg-primary inline-block shrink-0"></span>
                        {children}
                      </h3>
                    ),
                    p: ({ children }) => <p className="text-body-md leading-relaxed text-on-surface/90">{children}</p>,
                    ul: ({ children }) => (
                      <ul className="list-disc pl-6 space-y-2 marker:text-primary-container">
                        {children}
                      </ul>
                    ),
                    li: ({ children }) => <li className="text-body-md">{children}</li>,
                    blockquote: ({ children }) => (
                      <div className="p-6 my-4 bg-surface-container-high border border-outline-variant rounded-xl relative overflow-hidden group shadow-inner">
                        <div className="absolute top-0 right-0 p-4 opacity-20">
                          <span className="material-symbols-outlined text-primary">auto_awesome</span>
                        </div>
                        <h4 className="font-sans text-label-sm text-primary mb-2 uppercase tracking-wide">
                          AGENT REVIEW COMMENTARY
                        </h4>
                        <div className="text-sm italic font-body text-on-surface-variant/90">{children}</div>
                      </div>
                    ),
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-6 border border-outline-variant rounded-lg">
                        <table className="w-full text-left border-collapse bg-surface-container/30">
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className="bg-surface-container border-b border-outline-variant text-label-sm font-sans font-medium text-on-surface-variant">
                        {children}
                      </thead>
                    ),
                    tbody: ({ children }) => <tbody className="divide-y divide-white/5 font-sans">{children}</tbody>,
                    tr: ({ children }) => <tr className="hover:bg-white/5 transition-colors">{children}</tr>,
                    th: ({ children }) => <th className="px-4 py-3">{children}</th>,
                    td: ({ children }) => <td className="px-4 py-3 text-sm text-on-surface-variant">{children}</td>,
                  }}
                >
                  {displayedContent}
                </ReactMarkdown>
                <div ref={documentEndRef} />
              </article>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-on-surface-variant/50">
                <span className="material-symbols-outlined text-[48px] animate-spin mb-4 text-primary">
                  cycle
                </span>
                <p className="font-body text-body-lg">Initializing document generation process...</p>
                <p className="text-xs mt-1">Retrieving compliance guidelines & style rules from vector database</p>
              </div>
            )}
          </div>
        </section>

        {/* Column 3: Audit Panel */}
        <section className="w-1/4 flex flex-col gap-6">
          {/* Circular Score Panel */}
          <div className="bezel-card p-6 flex flex-col items-center justify-center text-center gap-4 relative overflow-hidden shrink-0">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-secondary-container to-transparent"></div>
            <h3 className="font-sans text-label-sm text-on-surface-variant uppercase tracking-wider">
              COMPLIANCE SCORE
            </h3>
            <div className="relative flex items-center justify-center">
              <svg className="w-32 h-32 transform -rotate-90">
                {/* Background track circle */}
                <circle
                  cx="64"
                  cy="64"
                  fill="transparent"
                  r="58"
                  stroke="rgba(255,255,255,0.05)"
                  strokeWidth="8"
                ></circle>
                {/* Foreground indicator circle */}
                <circle
                  className="text-primary drop-shadow-[0_0_8px_rgba(173,198,255,0.4)] transition-all duration-1000 ease-out"
                  cx="64"
                  cy="64"
                  fill="transparent"
                  r="58"
                  stroke="currentColor"
                  strokeWidth="8"
                  strokeDasharray="364.4"
                  strokeDashoffset={364.4 - (364.4 * (session?.scorecard?.score || 0)) / 100}
                ></circle>
              </svg>
              <span className="absolute text-3xl font-bold font-display">
                {session?.scorecard?.score || 0}
              </span>
            </div>
            <p className="text-xs text-on-surface-variant px-4 font-body">
              {session?.scorecard?.summary}
            </p>
          </div>

          {/* Audit Checklist Card */}
          <div className="bezel-card p-6 flex-1 flex flex-col gap-4 overflow-hidden">
            <h3 className="font-sans text-label-sm text-on-surface-variant uppercase tracking-wider shrink-0">
              AUDIT CHECKLIST
            </h3>
            <div className="space-y-4 overflow-y-auto custom-scrollbar flex-1 pr-1">
              {session?.scorecard?.checks?.map((check) => (
                <div
                  key={check.id}
                  className={`flex items-start gap-3 p-3 rounded-xl border transition-colors ${
                    check.status === "verified"
                      ? "bg-surface-container-high border-outline-variant"
                      : check.status === "attention"
                      ? "bg-surface-container-highest border-outline"
                      : "bg-surface-container border-outline-variant opacity-60"
                  }`}
                >
                  <span
                    className={`material-symbols-outlined mt-0.5 ${
                      check.status === "verified"
                        ? "text-primary"
                        : check.status === "attention"
                        ? "text-secondary"
                        : "text-outline"
                    }`}
                    style={{ fontVariationSettings: check.status !== "pending" ? "'FILL' 1" : "'FILL' 0" }}
                  >
                    {check.status === "verified"
                      ? "check_circle"
                      : check.status === "attention"
                      ? "info"
                      : "pending"}
                  </span>
                  <div className="flex flex-col">
                    <span className="font-display text-sm font-semibold text-on-surface">
                      {check.name}
                    </span>
                    <span
                      className={`font-sans text-[10px] uppercase font-bold tracking-wider mt-0.5 ${
                        check.status === "verified"
                          ? "text-primary"
                          : check.status === "attention"
                          ? "text-secondary"
                          : "text-on-surface-variant/60"
                      }`}
                    >
                      {check.status === "verified"
                        ? "Verified"
                        : check.status === "attention"
                        ? "Attention Required"
                        : "Pending"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      {/* Bottom Floating Dock (HITL Pause Gate) */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-4xl px-gutter z-40">
        <div className="bg-surface-container border border-outline-variant rounded-full p-3 flex items-center gap-4 shadow-[0_8px_32px_rgba(0,0,0,0.4)] ring-1 ring-white/5 backdrop-blur-xl">
          <div className="flex items-center gap-3 pl-6 pr-4 border-r border-outline-variant shrink-0">
            <div className="flex flex-col items-start">
              <span className="text-[9px] font-sans text-on-surface-variant uppercase tracking-tighter">
                System State
              </span>
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    session?.status === "running"
                      ? "bg-primary animate-spin"
                      : session?.status === "paused"
                      ? "bg-outline animate-pulse"
                      : session?.status === "completed"
                      ? "bg-primary"
                      : "bg-error"
                  }`}
                ></div>
                <span
                  className={`text-xs font-bold font-display uppercase ${
                    session?.status === "running"
                      ? "text-primary"
                      : session?.status === "paused"
                      ? "text-outline"
                      : session?.status === "completed"
                      ? "text-primary"
                      : "text-error"
                  }`}
                >
                  {session?.status === "running" ? "Running" : session?.status}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex-1 px-2">
            <input
              type="text"
              value={feedback}
              disabled={session?.status === "running" || session?.status === "completed"}
              onChange={(e) => setFeedback(e.target.value)}
              className="w-full bg-transparent border-none text-on-surface placeholder:text-on-surface-variant/40 focus:ring-0 font-body text-sm outline-none"
              placeholder={
                session?.status === "completed"
                  ? "Document pipeline successfully approved and completed."
                  : session?.status === "running"
                  ? "Writing and self-correcting constraints internally..."
                  : "Provide feedback or ask for a specific change..."
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") handleRequestRevision();
              }}
            />
          </div>

          <div className="flex items-center gap-2 pr-2 shrink-0">
            <button
              onClick={handleRequestRevision}
              disabled={session?.status === "running" || session?.status === "completed" || !feedback.trim()}
              className="px-5 py-2.5 rounded-full font-sans text-xs text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Request Revision
            </button>
            <button
              onClick={handleApprove}
              disabled={session?.status === "running" || session?.status === "completed"}
              className="px-6 py-2.5 bg-primary text-on-primary rounded-full font-sans text-xs shadow-lg hover:brightness-110 active:scale-95 transition-all flex items-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-sm">rocket_launch</span>
              <span>
                {session?.status === "completed" ? "Completed" : "Approve & Deploy"}
              </span>
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
