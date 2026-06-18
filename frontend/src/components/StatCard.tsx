import type { ReactNode } from "react";

type Props = {
  label: string;
  value: string | number;
  helper?: string;
  icon?: ReactNode;
};

export function StatCard({ label, value, helper, icon }: Props) {
  return (
    <section className="stat-card">
      <div className="stat-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
      {helper ? <small>{helper}</small> : null}
    </section>
  );
}
