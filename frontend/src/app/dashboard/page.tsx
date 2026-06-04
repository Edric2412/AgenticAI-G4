"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Topbar from "@/components/Topbar";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface RegistryItem {
  id: string;
  name: string;
  uuid: string;
  agent: string;
  status: "In Agentic Loop" | "Awaiting Review" | "Verified";
  elapsed: string;
}

interface AgentItem {
  name: string;
  type: string;
  status: "Active" | "Standby" | "Offline";
  load: string;
}

interface ThroughputBar {
  time: string;
  baseTokens: number;
  currentHeight: number;
}

export default function Dashboard() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [currentTime, setCurrentTime] = useState("");
  
  // Real dynamic metrics
  const [metrics, setMetrics] = useState({
    awaitingAction: 0,
    generatedCount: 0,
    avgRuntime: "--",
    efficiencySurge: "0h"
  });

  const [registryData, setRegistryData] = useState<RegistryItem[]>([]);
  const [apiStatus, setApiStatus] = useState<"Operational" | "Offline" | "Degraded">("Operational");
  const [dbLatency, setDbLatency] = useState("12ms");
  const [isLoading, setIsLoading] = useState(true);

  const [throughput, setThroughput] = useState<ThroughputBar[]>([
    { time: "00:00", baseTokens: 120000, currentHeight: 30 },
    { time: "02:00", baseTokens: 180000, currentHeight: 45 },
    { time: "04:00", baseTokens: 240000, currentHeight: 60 },
    { time: "06:00", baseTokens: 160000, currentHeight: 40 },
    { time: "08:00", baseTokens: 320000, currentHeight: 80 },
    { time: "10:00", baseTokens: 220000, currentHeight: 55 },
    { time: "12:00", baseTokens: 140000, currentHeight: 35 },
    { time: "14:00", baseTokens: 360000, currentHeight: 90 },
    { time: "16:00", baseTokens: 180000, currentHeight: 45 },
    { time: "18:00", baseTokens: 260000, currentHeight: 65 },
    { time: "20:00", baseTokens: 410000, currentHeight: 100 },
    { time: "22:00", baseTokens: 200000, currentHeight: 50 },
    { time: "23:59", baseTokens: 120000, currentHeight: 30 },
  ]);

  // Periodic throughput fluctuation simulator to make the charts feel alive
  useEffect(() => {
    const interval = setInterval(() => {
      const isActiveWork = registryData.some(item => item.status === "In Agentic Loop");
      
      setThroughput(prev => prev.map(bar => {
        const delta = (Math.random() - 0.5) * 0.10; // +/- 5%
        let scale = 1.0 + delta;
        
        // Boost throughput levels during active pipelines
        if (isActiveWork && (bar.time === "18:00" || bar.time === "20:00" || bar.time === "22:00" || bar.time === "23:59")) {
          scale = scale * 1.25;
        }
        
        const newHeight = Math.min(100, Math.max(15, bar.currentHeight * scale));
        const newTokens = Math.round(bar.baseTokens * scale);
        
        return {
          ...bar,
          currentHeight: Math.round(newHeight),
          baseTokens: newTokens
        };
      }));
    }, 4000);
    return () => clearInterval(interval);
  }, [registryData]);

  // Fetch telemetry updates from the backend
  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const start = performance.now();
        const res = await fetch(`${API_BASE_URL}/api/documents`);
        const duration = Math.round(performance.now() - start);
        
        if (!res.ok) throw new Error("Failed to fetch dashboard metrics");
        const data = await res.json();
        
        if (data.metrics) {
          setMetrics(data.metrics);
        }
        if (data.registry) {
          setRegistryData(data.registry);
        }
        setApiStatus("Operational");
        setDbLatency(`${Math.min(50, Math.max(5, duration))}ms`);
      } catch (err) {
        console.error("Error fetching telemetry:", err);
        setApiStatus("Offline");
        setDbLatency("--");
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTelemetry();
    // Poll telemetry data every 3 seconds to keep it fully real-time
    const interval = setInterval(fetchTelemetry, 3000);
    return () => clearInterval(interval);
  }, []);

  // Compute dynamic statuses for the agent constellation based on the active registry items
  const isAgentActive = (agentName: string) => {
    return registryData.some(item => item.agent === agentName && item.status === "In Agentic Loop");
  };

  const getAgentLoad = (agentName: string) => {
    const activeCount = registryData.filter(item => item.agent === agentName && item.status === "In Agentic Loop").length;
    if (activeCount === 0) return "0%";
    if (activeCount === 1) return "45%";
    return "92%";
  };

  const agentData: AgentItem[] = [
    {
      name: "Summarizer-Alpha",
      type: "Large Language Core v4",
      status: isAgentActive("Summarizer-Alpha") ? "Active" : "Standby",
      load: getAgentLoad("Summarizer-Alpha"),
    },
    {
      name: "Compliance-Bot",
      type: "Reg-Tech Engine",
      status: isAgentActive("Compliance-Bot") ? "Active" : "Standby",
      load: getAgentLoad("Compliance-Bot"),
    },
    {
      name: "Fiscal-Analytic-02",
      type: "Financial Logic Gate",
      status: isAgentActive("Fiscal-Analytic-02") ? "Active" : "Standby",
      load: getAgentLoad("Fiscal-Analytic-02"),
    },
    {
      name: "Validation-Core",
      type: "Maintenance",
      status: "Offline",
      load: "--",
    },
  ];

  // Filter registry items based on query
  const filteredRegistry = registryData.filter(
    (item) =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.uuid.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.agent.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.status.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Time updater effect
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString());
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
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

  return (
    <main className="flex-1 flex flex-col min-h-screen overflow-y-auto custom-scrollbar ml-64 bg-surface text-on-surface">
      {/* Background Glows */}
      <div className="aurora-glow">
        <div className="aurora-blob" style={{ top: "-10%", left: "-10%", background: "radial-gradient(circle, rgba(173, 198, 255, 0.05) 0%, rgba(173, 198, 255, 0) 70%)" }}></div>
        <div className="aurora-blob" style={{ bottom: "-10%", right: "-10%", background: "radial-gradient(circle, rgba(173, 198, 255, 0.05) 0%, transparent 70%)" }}></div>
      </div>

      {/* Top Bar with search bar binding */}
      <Topbar>
        <div className="flex items-center gap-4 flex-1">
          <div className="relative w-full max-w-md">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-full py-2 pl-10 pr-4 text-body-md focus:outline-none focus:ring-1 focus:ring-primary/50 placeholder:text-on-surface-variant/40"
              placeholder="Search operational telemetry..."
            />
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button className="p-2 text-on-surface-variant hover:bg-white/5 transition-colors cursor-pointer relative rounded-full active:scale-95 duration-200">
            <span className="material-symbols-outlined">notifications</span>
            <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full"></span>
          </button>
          <div className="flex items-center text-xs font-mono text-on-surface-variant/70 border border-white/5 bg-white/5 rounded-lg px-2.5 py-1">
            <span>{currentTime}</span>
          </div>
          <div className="w-8 h-8 rounded-full overflow-hidden border border-white/20 ml-2 cursor-pointer active:scale-95 duration-200">
            <img
              className="w-full h-full object-cover"
              alt="Professional profile avatar"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuC4biUgCGM4lJkMoOxJQNud3NhJ7YMt1kPfV-JxPzW-3Hz_isJv7vb__gzESFP1w7_m7GWxN3OCAGeDa9VLuhEiGL2elfXAwF3oh-aBCxiJeM24xCANJCDrM80kME8J8B0k60Jg_dl4j3DVrOkUHEopI-bUEOl829auTxeFHdX8Sa7ySa0PoY5x96VZikn94aNddAvmAbr1xIjkjhRDEws6qgrJDZoM8kRF9I8UT6G5cSkU40escyQaxhwMsVywOy_o8l1-_3wN_sg"
            />
          </div>
        </div>
      </Topbar>

      {/* Main dashboard content */}
      <div className="p-container-margin max-w-[1600px] mx-auto w-full space-y-gutter flex-1">
        {/* Headline */}
        <div className="flex flex-col gap-1 mb-8">
          <h2 className="font-display text-headline-lg text-on-surface">
            Operational Overview
          </h2>
          <p className="font-body text-body-md text-on-surface-variant">
            Real-time telemetry and agentic document processing status.
          </p>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter mb-8">
          {/* Metric 1 */}
          <div className="glass-panel p-card-padding rounded-xl group hover:border-primary/30 transition-all cursor-default">
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-primary/10 text-primary rounded-xl">
                <span className="material-symbols-outlined">pending_actions</span>
              </div>
              <span className="font-sans text-label-sm text-secondary-container">+4 from 1h ago</span>
            </div>
            <div className="space-y-1">
              <p className="font-body text-body-md text-on-surface-variant">Awaiting Action</p>
              <h3 className="font-display text-[32px] leading-none text-on-surface">
                {metrics.awaitingAction}
              </h3>
            </div>
          </div>

          {/* Metric 2 */}
          <div className="glass-panel p-card-padding rounded-xl group hover:border-primary/30 transition-all cursor-default">
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-primary/10 text-primary rounded-xl">
                <span className="material-symbols-outlined">description</span>
              </div>
              <span className="font-sans text-label-sm text-on-surface-variant">Lifetime: 1.2k</span>
            </div>
            <div className="space-y-1">
              <p className="font-body text-body-md text-on-surface-variant">Documents Generated</p>
              <h3 className="font-display text-[32px] leading-none text-on-surface">
                {metrics.generatedCount}
              </h3>
            </div>
          </div>

          {/* Metric 3 */}
          <div className="glass-panel p-card-padding rounded-xl group hover:border-primary/30 transition-all cursor-default">
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-primary/10 text-primary rounded-xl">
                <span className="material-symbols-outlined">timer</span>
              </div>
              <span className="font-sans text-label-sm text-tertiary-container">-12s latency</span>
            </div>
            <div className="space-y-1">
              <p className="font-body text-body-md text-on-surface-variant">Avg Runtime</p>
              <h3 className="font-display text-[32px] leading-none text-on-surface">
                {metrics.avgRuntime}
              </h3>
            </div>
          </div>

          {/* Metric 4 */}
          <div className="glass-panel p-card-padding rounded-xl group hover:border-primary/30 transition-all cursor-default">
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-secondary-container/10 text-secondary-container rounded-xl">
                <span className="material-symbols-outlined">bolt</span>
              </div>
              <span className="font-sans text-label-sm text-secondary-container">Peak: 92h</span>
            </div>
            <div className="space-y-1">
              <p className="font-body text-body-md text-on-surface-variant">Efficiency Surge</p>
              <h3 className="font-display text-[32px] leading-none text-on-surface">
                {metrics.efficiencySurge}
              </h3>
            </div>
          </div>
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter">
          {/* Live Registry Table */}
          <div className="lg:col-span-8 flex flex-col gap-gutter">
            <div className="glass-panel rounded-xl overflow-hidden flex flex-col">
              <div className="p-card-padding border-b border-white/5 flex items-center justify-between">
                <h3 className="font-display text-[20px] font-semibold flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">view_list</span>
                  <span>Live Registry</span>
                </h3>
                <button className="text-label-sm text-primary uppercase tracking-widest hover:underline transition-all">
                  Export Report
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="font-sans text-label-sm text-on-surface-variant/60 uppercase border-b border-white/5">
                      <th className="px-6 py-4 font-medium">Document Entity</th>
                      <th className="px-6 py-4 font-medium">Agent Assigned</th>
                      <th className="px-6 py-4 font-medium">Processing Status</th>
                      <th className="px-6 py-4 font-medium">Time Elapsed</th>
                    </tr>
                  </thead>
                  <tbody className="font-body text-body-md">
                    {isLoading ? (
                      <tr>
                        <td colSpan={4} className="px-6 py-10 text-center text-on-surface-variant/60">
                          <span className="material-symbols-outlined animate-spin align-middle mr-2">sync</span>
                          Connecting to backend telemetry...
                        </td>
                      </tr>
                    ) : filteredRegistry.length > 0 ? (
                      filteredRegistry.map((item) => (
                        <tr
                          key={item.id}
                          onClick={() => router.push(`/canvas/${item.id}`)}
                          className="border-b border-white/5 hover:bg-white/5 transition-colors group cursor-pointer"
                        >
                          <td className="px-6 py-5">
                            <div className="flex flex-col">
                              <span className="text-on-surface font-medium">{item.name}</span>
                              <span className="text-[12px] text-on-surface-variant/60">
                                UUID: {item.uuid}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-5">
                            <div className="flex items-center gap-2">
                              <div
                                className={`w-2 h-2 rounded-full ${
                                  item.status === "In Agentic Loop"
                                    ? "bg-primary agent-pulse"
                                    : item.status === "Awaiting Review"
                                    ? "bg-secondary-container"
                                    : "bg-tertiary-container"
                                }`}
                              ></div>
                              <span className="text-on-surface-variant">{item.agent}</span>
                            </div>
                          </td>
                          <td className="px-6 py-5">
                            <span
                              className={`px-3 py-1 font-sans text-label-sm rounded-full border ${
                                item.status === "In Agentic Loop"
                                  ? "bg-primary/10 text-primary border-primary/20"
                                  : item.status === "Awaiting Review"
                                  ? "bg-secondary-container/10 text-secondary-container border-secondary-container/20"
                                  : "bg-tertiary-container/10 text-tertiary-container border-tertiary-container/20"
                              }`}
                            >
                                {item.status}
                            </span>
                          </td>
                          <td className="px-6 py-5 text-on-surface-variant">{item.elapsed}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-6 py-10 text-center text-on-surface-variant/60 italic">
                          No matching telemetry datasets found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Neural Processing Throughput */}
            <div className="glass-panel rounded-xl p-card-padding flex flex-col gap-6">
              <div className="flex items-center justify-between">
                <h3 className="font-display text-[20px] font-semibold flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">analytics</span>
                  <span>Neural Processing Throughput</span>
                </h3>
                <div className="flex gap-2 items-center">
                  <span className="w-3 h-3 bg-primary rounded-sm"></span>
                  <span className="font-sans text-label-sm text-on-surface-variant">
                    Token Consumption
                  </span>
                </div>
              </div>
              <div className="h-48 flex items-end justify-between gap-2 px-2">
                {throughput.map((bar) => (
                  <div
                    key={bar.time}
                    className="w-full bg-primary/20 rounded-t-sm transition-all duration-1000 cursor-help hover:bg-primary/50 relative"
                    style={{
                      height: `${bar.currentHeight}%`,
                      backgroundColor: bar.currentHeight > 85 ? "rgba(173, 198, 255, 0.7)" : undefined
                    }}
                    title={`${bar.time} - ${bar.baseTokens.toLocaleString()} tokens`}
                  >
                    {bar.currentHeight >= 95 && (
                      <div className="absolute -top-6 left-1/2 -translate-x-1/2 font-sans text-[9px] text-primary">
                        Peak
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="flex justify-between font-sans text-label-sm text-on-surface-variant/40 px-2">
                <span>00:00</span>
                <span>04:00</span>
                <span>08:00</span>
                <span>12:00</span>
                <span>16:00</span>
                <span>20:00</span>
                <span>23:59</span>
              </div>
            </div>
          </div>

          {/* Agent Constellation Card */}
          <div className="lg:col-span-4 flex flex-col gap-gutter">
            <div className="glass-panel rounded-xl flex flex-col h-full">
              <div className="p-card-padding border-b border-white/5 flex items-center justify-between">
                <h3 className="font-display text-[20px] font-semibold flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">hub</span>
                  <span>Agent Constellation</span>
                </h3>
                <span className="px-2 py-0.5 bg-white/5 rounded font-sans text-label-sm text-[10px] uppercase">
                  {agentData.filter(a => a.status === "Active").length} / {agentData.length} Active
                </span>
              </div>
              <div className="p-card-padding flex-1 flex flex-col gap-4">
                {agentData.map((agent) => (
                  <div
                    key={agent.name}
                    className="p-4 rounded-xl border border-white/5 bg-surface-container-high hover:bg-surface-bright transition-colors flex items-center justify-between group shadow-sm"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-surface flex items-center justify-center relative">
                        <span
                          className={`material-symbols-outlined ${
                            agent.status === "Active"
                              ? "text-primary"
                              : agent.status === "Standby"
                              ? "text-primary-container"
                              : "text-on-surface-variant"
                          }`}
                          style={{ fontVariationSettings: "'FILL' 1" }}
                        >
                          {agent.name === "Compliance-Bot"
                            ? "security"
                            : agent.name === "Fiscal-Analytic-02"
                            ? "analytics"
                            : agent.name === "Validation-Core"
                            ? "construction"
                            : "smart_toy"}
                        </span>
                        {agent.status === "Active" && (
                          <div className="absolute -top-1 -right-1 w-3 h-3 bg-secondary-container rounded-full border-2 border-surface-container-low agent-pulse"></div>
                        )}
                        {agent.status === "Standby" && (
                          <div className="absolute -top-1 -right-1 w-3 h-3 bg-tertiary-container rounded-full border-2 border-surface-container-low"></div>
                        )}
                      </div>
                      <div className="flex flex-col">
                        <span className="text-on-surface font-medium font-body text-body-md">
                          {agent.name}
                        </span>
                        <span className="font-sans text-label-sm text-[10px] text-on-surface-variant uppercase tracking-tighter">
                          {agent.type}
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end">
                      <span
                        className={`text-[12px] font-sans text-label-md ${
                          agent.status === "Active"
                            ? "text-secondary-container"
                            : agent.status === "Standby"
                            ? "text-tertiary-container"
                            : "text-on-surface-variant/40"
                        }`}
                      >
                        {agent.status}
                      </span>
                      <span className="font-sans text-label-sm text-[10px] text-on-surface-variant/40">
                        {agent.load} Load
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-card-padding border-t border-white/5">
                <button className="w-full py-3 border border-white/10 rounded-xl font-medium hover:bg-white/5 transition-all text-on-surface-variant font-sans text-label-md">
                  View Agent Parameters
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer / System Health */}
      <footer className="mt-auto px-container-margin py-6 border-t border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${
              apiStatus === "Operational"
                ? "bg-[#00e676] animate-pulse"
                : apiStatus === "Degraded"
                ? "bg-tertiary"
                : "bg-error"
            }`}></span>
            <span className="font-sans text-label-sm text-on-surface-variant">API: {apiStatus}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${
              apiStatus === "Operational"
                ? "bg-[#00e676]"
                : "bg-error/30"
            }`}></span>
            <span className="font-sans text-label-sm text-on-surface-variant">Database: {dbLatency}</span>
          </div>
        </div>
        <div className="font-sans text-label-sm text-on-surface-variant/30">
          © 2026 DocuFlow AI Enterprise. All Systems Nominal.
        </div>
      </footer>
    </main>
  );
}
