interface Props {
  text?: string;
}

export function Headline({ text }: Props) {
  if (!text) return null;
  return (
    <div className="mb-8 px-5 py-4 rounded-xl border border-border bg-card/50">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
        The Verdict
      </p>
      <p className="text-base font-medium leading-relaxed">{text}</p>
    </div>
  );
}
