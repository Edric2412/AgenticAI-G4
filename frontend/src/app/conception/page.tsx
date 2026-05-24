"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Topbar from "@/components/Topbar";

type Archetype = "Technical" | "Legal" | "Financial" | "Creative";

export default function ConceptionHub() {
  const router = useRouter();
  
  // Form State
  const [archetype, setArchetype] = useState<Archetype>("Technical");
  const [loopGuard, setLoopGuard] = useState(3);
  const [semanticEnrichment, setSemanticEnrichment] = useState(true);
  const [conflictDetection, setConflictDetection] = useState(false);
  const [payloadText, setPayloadText] = useState("");
  
  // Footer Telemetry State
  const [tokenCount, setTokenCount] = useState(12482);
  const [activeTab, setActiveTab] = useState<"Raw Input" | "Preview Schema" | "Metadata Tags">("Raw Input");

  // Time-based simulated token increment
  useEffect(() => {
    const interval = setInterval(() => {
      setTokenCount((prev) => prev + Math.floor(Math.random() * 5));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Aurora blobs mouse follow effect
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const blobs = document.querySelectorAll(".aurora-blob");
      const x = e.clientX / window.innerWidth;
      const y = e.clientY / window.innerHeight;

      blobs.forEach((blob, index) => {
        const speed = (index + 1) * 20;
        (blob as HTMLElement).style.transform = `translate(${x * speed}px, ${y * speed}px)`;
      });
    };
    document.addEventListener("mousemove", handleMouseMove);
    return () => document.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // Mouse trail glow inside textarea container
  const handleEditorMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const glow = document.createElement("div");
    glow.className = "aurora-glow pointer-events-none absolute w-36 h-36 rounded-full bg-primary/10 blur-xl";
    glow.style.left = `${x - 72}px`;
    glow.style.top = `${y - 72}px`;
    glow.style.opacity = "0.2";
    glow.style.zIndex = "10";

    e.currentTarget.appendChild(glow);
    setTimeout(() => glow.remove(), 1000);
  };

  // Submission handler
  const handleStartPipeline = async () => {
    // Generate a mock sessionId to simulate FastAPI LangGraph checkpoint instantiations
    const mockSessionId = "dfl_" + Math.random().toString(36).substring(2, 11);
    
    // Redirect to Page 3 (Agentic Canvas)
    router.push(`/canvas/${mockSessionId}`);
  };

  const handleClearWorkspace = () => {
    setPayloadText("");
  };

  return (
    <main className="flex-1 flex flex-col relative overflow-hidden bg-background ml-64 pt-16 h-screen w-screen">
      {/* Background Glows */}
      <div className="aurora-glow">
        <div className="aurora-blob bg-primary/20 top-0 left-1/4"></div>
        <div className="aurora-blob bg-secondary/20 bottom-0 right-1/4" style={{ animationDelay: "-3s" }}></div>
      </div>

      {/* TopAppBar */}
      <Topbar>
        <div className="flex items-center gap-4">
          <h1 className="font-display text-headline-lg font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Conception Hub
          </h1>
          <div className="h-4 w-px bg-white/10"></div>
          <div className="flex items-center gap-2 text-on-surface-variant font-sans text-label-md">
            <span className="material-symbols-outlined text-[18px]">folder_open</span>
            <span>root / conception_v2 / pipeline_init</span>
          </div>
        </div>
        <div className="flex items-center gap-gutter">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/5">
            <div className="w-2 h-2 rounded-full bg-secondary agent-pulse"></div>
            <span className="font-sans text-label-sm text-secondary">Agent Ready</span>
          </div>
          <div className="flex gap-2">
            <span className="material-symbols-outlined p-2 text-on-surface-variant hover:bg-white/5 transition-colors cursor-pointer rounded-full active:scale-95 duration-200">
              notifications
            </span>
            <span className="material-symbols-outlined p-2 text-on-surface-variant hover:bg-white/5 transition-colors cursor-pointer rounded-full active:scale-95 duration-200">
              account_circle
            </span>
          </div>
        </div>
      </Topbar>

      {/* Content Canvas */}
      <div className="flex-1 flex overflow-hidden p-container-margin gap-gutter pb-4">
        
        {/* Left Panel: Pipeline Configuration */}
        <section className="w-80 flex flex-col gap-gutter shrink-0 overflow-y-auto custom-scrollbar">
          <div className="liquid-glass rounded-xl p-card-padding flex flex-col gap-gutter">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[20px]">
                account_tree
              </span>
              <h2 className="font-display text-headline-lg-mobile font-semibold">
                Pipeline Settings
              </h2>
            </div>
            
            {/* Document Archetype */}
            <div className="flex flex-col gap-unit">
              <label className="font-sans text-label-sm text-on-surface-variant uppercase tracking-wider">
                Document Archetype
              </label>
              <div className="grid grid-cols-2 gap-2">
                {(["Technical", "Legal", "Financial", "Creative"] as Archetype[]).map((type) => {
                  const isActive = archetype === type;
                  return (
                    <button
                      key={type}
                      onClick={() => setArchetype(type)}
                      className={`p-3 rounded border text-center flex flex-col items-center gap-1 transition-all ${
                        isActive
                          ? "border-primary bg-primary/5 text-primary"
                          : "border-white/10 hover:border-white/20 text-on-surface-variant"
                      }`}
                    >
                      <span className="material-symbols-outlined">
                        {type === "Technical"
                          ? "terminal"
                          : type === "Legal"
                          ? "gavel"
                          : type === "Financial"
                          ? "payments"
                          : "palette"}
                      </span>
                      <span className="font-sans text-label-sm">{type}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Agent Loop Guard Slider */}
            <div className="flex flex-col gap-unit mt-2">
              <div className="flex justify-between items-center">
                <label className="font-sans text-label-sm text-on-surface-variant uppercase tracking-wider">
                  Agent Loop Guard
                </label>
                <span className="font-sans text-label-sm text-primary">
                  {loopGuard} Cycles
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                value={loopGuard}
                onChange={(e) => setLoopGuard(parseInt(e.target.value))}
                className="w-full accent-primary h-1.5 bg-surface-container-highest rounded-lg cursor-pointer"
              />
              <p className="text-[11px] text-on-surface-variant/60 leading-relaxed font-body">
                Defines the maximum recursive iterations the agent will perform for data validation and self-correction checks.
              </p>
            </div>

            <div className="h-px bg-white/5 my-2"></div>

            {/* Augmentation Modules */}
            <div className="flex flex-col gap-unit">
              <label className="font-sans text-label-sm text-on-surface-variant uppercase tracking-wider">
                Augmentation Modules
              </label>
              <div className="flex flex-col gap-2">
                <label className="flex items-center justify-between p-2 rounded hover:bg-white/5 cursor-pointer transition-colors">
                  <span className="font-body text-body-md text-on-surface">Semantic Enrichment</span>
                  <input
                    type="checkbox"
                    checked={semanticEnrichment}
                    onChange={(e) => setSemanticEnrichment(e.target.checked)}
                    className="rounded border-white/20 bg-transparent text-primary focus:ring-0 w-4 h-4 cursor-pointer"
                  />
                </label>
                <label className="flex items-center justify-between p-2 rounded hover:bg-white/5 cursor-pointer transition-colors">
                  <span className="font-body text-body-md text-on-surface">Conflict Detection</span>
                  <input
                    type="checkbox"
                    checked={conflictDetection}
                    onChange={(e) => setConflictDetection(e.target.checked)}
                    className="rounded border-white/20 bg-transparent text-primary focus:ring-0 w-4 h-4 cursor-pointer"
                  />
                </label>
              </div>
            </div>
          </div>

          {/* Processor Card */}
          <div className="liquid-glass rounded-xl p-card-padding flex items-center gap-4">
            <img
              className="w-12 h-12 rounded bg-surface-container-highest object-cover"
              alt="AI Core Chip"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuAzJngotTTBoO2gvdPjmSw_RUvStO6r5vwsByclhdPwIHkx_qhvrRLlbyNN2HQrMvh5MeGrVVNwI3R-IpNN3f3IlD_AFDswTpra56i4Y3GzmET8FGjLWi6RD1Aur9INAo43clr6lq1xMYLpVRkXwdxtVL3ZqUy_P-2fpErr98tNK_Xhd-aGA9ggh6qp3FSexTtb7PbctrH2hmq09fl6EmFiA3JtWbwcme0RgbMrOQ2IkTsM8wcqlBJSlAib2H6m1UEWP9pqVhPjCa8"
            />
            <div className="flex flex-col">
              <span className="font-sans text-label-md text-on-surface font-semibold">Project Obsidian</span>
              <span className="font-sans text-[10px] text-on-surface-variant uppercase">Active Deployment</span>
            </div>
          </div>
        </section>

        {/* Main Area: Ingestion Payload */}
        <section className="flex-1 flex flex-col gap-gutter relative">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/20 rounded-lg">
                <span className="material-symbols-outlined text-primary">input_circle</span>
              </div>
              <div>
                <h2 className="font-display text-headline-lg font-semibold tracking-tight">
                  Context Ingestion Payload
                </h2>
                <p className="font-body text-body-md text-on-surface-variant">
                  Paste raw source documentation, technical specifications, or compliance guidelines.
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleClearWorkspace}
                className="px-4 py-2 rounded-full border border-white/10 hover:bg-white/5 transition-all font-sans text-label-md cursor-pointer"
              >
                Clear Workspace
              </button>
              <button
                onClick={handleStartPipeline}
                className="px-6 py-2 rounded-full bg-primary text-on-primary font-sans text-label-md font-semibold shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all cursor-pointer"
              >
                Start Pipeline
              </button>
            </div>
          </div>

          {/* Large Editor Area with tabs */}
          <div
            onMouseMove={handleEditorMouseMove}
            className="flex-1 liquid-glass rounded-2xl overflow-hidden flex flex-col relative"
          >
            <div className="h-10 bg-white/5 border-b border-white/5 flex items-center px-4 justify-between select-none">
              <div className="flex gap-4 h-full">
                {(["Raw Input", "Preview Schema", "Metadata Tags"] as const).map((tab) => {
                  const isActive = activeTab === tab;
                  return (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`font-sans text-[11px] h-full flex items-center px-1 transition-all cursor-pointer ${
                        isActive
                          ? "text-primary border-b border-primary"
                          : "text-on-surface-variant hover:text-on-surface"
                      }`}
                    >
                      {tab}
                    </button>
                  );
                })}
              </div>
              <div className="flex gap-3">
                <span className="material-symbols-outlined text-[16px] text-on-surface-variant hover:text-on-surface cursor-pointer" title="Upload Document">
                  file_upload
                </span>
                <span
                  onClick={() => navigator.clipboard.writeText(payloadText)}
                  className="material-symbols-outlined text-[16px] text-on-surface-variant hover:text-on-surface cursor-pointer"
                  title="Copy Content"
                >
                  content_copy
                </span>
              </div>
            </div>

            {activeTab === "Raw Input" ? (
              <textarea
                value={payloadText}
                onChange={(e) => setPayloadText(e.target.value)}
                className="flex-1 bg-transparent p-6 font-body text-body-md leading-relaxed text-on-surface outline-none border-none resize-none placeholder:text-white/10 scroll-smooth custom-scrollbar"
                placeholder={`Paste your source context here...

// Example: Technical Requirement Specification v4.2
// Target: LLM Orchestration Layer
// Scope: Multi-agent state synchronization via SSE...`}
              />
            ) : activeTab === "Preview Schema" ? (
              <div className="flex-1 p-6 font-mono text-xs text-on-surface-variant overflow-y-auto custom-scrollbar">
                <pre>{`{
  "archetype": "${archetype.toLowerCase()}",
  "loop_guard": ${loopGuard},
  "modules": {
    "semantic_enrichment": ${semanticEnrichment},
    "conflict_detection": ${conflictDetection}
  },
  "payload_length": ${payloadText.length}
}`}</pre>
              </div>
            ) : (
              <div className="flex-1 p-6 flex flex-wrap gap-2 content-start overflow-y-auto custom-scrollbar">
                <span className="px-3 py-1 rounded bg-white/5 border border-white/10 text-xs font-mono text-primary">#archetype:{archetype.toLowerCase()}</span>
                <span className="px-3 py-1 rounded bg-white/5 border border-white/10 text-xs font-mono text-secondary">#loops:{loopGuard}</span>
                {semanticEnrichment && <span className="px-3 py-1 rounded bg-white/5 border border-white/10 text-xs font-mono text-tertiary">#semantic-enrichment</span>}
                {conflictDetection && <span className="px-3 py-1 rounded bg-white/5 border border-white/10 text-xs font-mono text-error">#conflict-detection</span>}
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Bottom Status Bar */}
      <footer className="h-10 bg-surface-container-lowest border-t border-white/5 flex items-center justify-between px-container-margin z-40 shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="font-sans text-[10px] text-on-surface-variant uppercase tracking-widest">
              Token Count:
            </span>
            <span className="font-sans text-label-md text-on-surface">
              {tokenCount.toLocaleString()} / 128k
            </span>
            <div className="w-24 h-1 bg-white/5 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-500"
                style={{ width: `${Math.min(100, (tokenCount / 128000) * 100)}%` }}
              ></div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-sans text-[10px] text-on-surface-variant uppercase tracking-widest">
              Entropy Level:
            </span>
            <span className="font-sans text-label-md text-tertiary">0.245 (Low)</span>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="font-sans text-[10px] text-on-surface-variant uppercase tracking-widest">
              Region:
            </span>
            <span className="font-sans text-label-md text-on-surface flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">public</span>
              <span>AWS-US-EAST-1</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-sans text-[10px] text-on-surface-variant uppercase tracking-widest">
              System Load:
            </span>
            <span className="font-sans text-label-md text-on-surface">14%</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
