"use client";
import { useEffect, useState } from "react";

interface PersonaOption {
  key: string;
  name: string;
  tagline: string;
}

interface Props {
  value: string;
  onChange: (key: string) => void;
}

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function PersonaSelector({ value, onChange }: Props) {
  const [personas, setPersonas] = useState<PersonaOption[]>([]);

  useEffect(() => {
    fetch(`${BASE}/personas`)
      .then((r) => r.json())
      .then(setPersonas)
      .catch(() => {/* non-critical */});
  }, []);

  return (
    <div className="flex flex-col items-center gap-1.5 mb-6">
      <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
        Analyze through the lens of
      </p>
      <div className="flex flex-wrap gap-2 justify-center">
        <button
          onClick={() => onChange("default")}
          className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
            value === "default"
              ? "bg-foreground text-background border-foreground"
              : "border-border text-muted-foreground hover:border-foreground/50 hover:text-foreground"
          }`}
        >
          Default
        </button>
        {personas.map((p) => (
          <button
            key={p.key}
            title={p.tagline}
            onClick={() => onChange(p.key)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
              value === p.key
                ? "bg-foreground text-background border-foreground"
                : "border-border text-muted-foreground hover:border-foreground/50 hover:text-foreground"
            }`}
          >
            {p.name}
          </button>
        ))}
      </div>
      {value !== "default" && (
        <p className="text-xs text-muted-foreground italic mt-0.5">
          {personas.find((p) => p.key === value)?.tagline}
        </p>
      )}
    </div>
  );
}
