"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: "dashboard" },
    { name: "Conception Hub", href: "/conception", icon: "hub" },
    { name: "Audit Logs", href: "#", icon: "history" },
    { name: "Settings", href: "#", icon: "settings" },
  ];

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-surface-container/80 backdrop-blur-[32px] border-r border-white/10 shadow-2xl flex flex-col py-6 space-y-4 z-50">
      <div className="flex items-center gap-3 px-6 mb-4">
        <div className="w-10 h-10 rounded-lg bg-primary-container flex items-center justify-center text-on-primary shadow-lg shadow-primary/20">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
            fluid
          </span>
        </div>
        <div>
          <h1 className="font-display text-[22px] leading-tight font-black text-on-surface">
            DocuFlow AI
          </h1>
          <p className="font-sans text-[10px] uppercase tracking-widest text-on-surface-variant/60">
            Enterprise Suite
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 font-sans text-label-md transition-all duration-300 group hover:bg-white/5 ${
                isActive
                  ? "bg-primary-container/20 text-primary border-l-4 border-primary"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
            >
              <span
                className="material-symbols-outlined transition-transform group-hover:translate-x-1 duration-200"
                style={{
                  fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
                }}
              >
                {item.icon}
              </span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="px-6 pb-4">
        <Link
          href="/conception"
          className="w-full py-3 bg-primary text-on-primary font-medium rounded-xl shadow-lg shadow-primary/10 hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-2 text-center"
        >
          <span className="material-symbols-outlined text-[20px]">
            add_circle
          </span>
          <span>Initialize Pipeline</span>
        </Link>
      </div>
    </aside>
  );
}
