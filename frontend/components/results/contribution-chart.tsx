"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { FeatureContribution } from "@/types/assessment";

export function ContributionChart({
  contributions,
}: {
  contributions: FeatureContribution[];
}) {
  const data = contributions.slice(0, 8).map((item) => ({
    name: item.feature.replaceAll("_", " "),
    value: Number(item.contribution.toFixed(4)),
    direction: item.direction,
  }));

  if (!data.length) {
    return <p className="text-sm text-[var(--muted)]">No contribution data is available.</p>;
  }

  return (
    <div className="h-80 w-full" aria-label="Feature contribution chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 20, right: 12 }}>
          <CartesianGrid horizontal={false} stroke="#d8e4de" />
          <XAxis type="number" tick={{ fontSize: 11, fill: "#60736c" }} />
          <YAxis
            type="category"
            dataKey="name"
            width={130}
            tick={{ fontSize: 11, fill: "#60736c" }}
          />
          <Tooltip
            formatter={(value) => [Number(value).toFixed(4), "Contribution"]}
            contentStyle={{ borderRadius: 12, borderColor: "#d8e4de" }}
          />
          <Bar dataKey="value" radius={[0, 5, 5, 0]}>
            {data.map((item) => (
              <Cell
                key={item.name}
                fill={item.direction === "risk_increasing" ? "#b7791f" : "#126b50"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
