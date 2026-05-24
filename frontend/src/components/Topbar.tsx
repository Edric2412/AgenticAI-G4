import React from "react";

interface TopbarProps {
  children?: React.ReactNode;
}

export default function Topbar({ children }: TopbarProps) {
  return (
    <header className="sticky top-0 z-40 flex justify-between items-center px-container-margin h-16 bg-surface/70 backdrop-blur-[32px] border-b border-white/10 shadow-[0_40px_40px_-15px_rgba(47,46,190,0.2)] w-full">
      {children}
    </header>
  );
}
