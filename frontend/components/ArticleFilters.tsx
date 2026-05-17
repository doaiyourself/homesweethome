"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

import { cn } from "@/lib/utils";

const TRADE_OPTIONS = [
  { value: "A1", label: "매매" },
  { value: "B1", label: "전세" },
  { value: "B2", label: "월세" },
];

const STATUS_OPTIONS = [
  { value: "active", label: "활성" },
  { value: "new", label: "24h 신규" },
  { value: "all", label: "전체" },
];

const SORT_OPTIONS = [
  { value: "score", label: "점수순" },
  { value: "date", label: "신규순" },
  { value: "last_seen", label: "갱신순" },
];

export function ArticleFilters() {
  const router = useRouter();
  const params = useSearchParams();

  const status = params.get("status") ?? "active";
  const sort = params.get("sort") ?? "score";
  const minScore = params.get("min_score") ?? "";
  const tradeTypes = new Set(params.getAll("trade_type"));

  const updateParam = useCallback(
    (key: string, value: string | null) => {
      const next = new URLSearchParams(params.toString());
      next.delete("page"); // reset pagination on filter change
      if (value === null || value === "") next.delete(key);
      else next.set(key, value);
      router.push(`/articles?${next.toString()}`);
    },
    [params, router],
  );

  const toggleTrade = (value: string) => {
    const next = new URLSearchParams(params.toString());
    next.delete("page");
    const current = next.getAll("trade_type");
    next.delete("trade_type");
    if (current.includes(value)) {
      for (const v of current.filter((v) => v !== value))
        next.append("trade_type", v);
    } else {
      for (const v of current) next.append("trade_type", v);
      next.append("trade_type", value);
    }
    router.push(`/articles?${next.toString()}`);
  };

  return (
    <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-900">
      <ToggleGroup
        label="상태"
        options={STATUS_OPTIONS}
        active={status}
        onChange={(v) => updateParam("status", v === "active" ? null : v)}
      />
      <ToggleGroup
        label="정렬"
        options={SORT_OPTIONS}
        active={sort}
        onChange={(v) => updateParam("sort", v === "score" ? null : v)}
      />
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
          거래
        </span>
        {TRADE_OPTIONS.map((opt) => {
          const on = tradeTypes.has(opt.value);
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => toggleTrade(opt.value)}
              className={cn(
                "rounded-md border px-2.5 py-1 text-xs transition",
                on
                  ? "border-blue-300 bg-blue-50 text-blue-800 dark:border-blue-700 dark:bg-blue-900 dark:text-blue-100"
                  : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300",
              )}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
      <div className="flex items-center gap-2">
        <label className="text-xs font-medium text-gray-500 dark:text-gray-400">
          최소 점수
        </label>
        <input
          type="number"
          min={0}
          max={100}
          step={5}
          defaultValue={minScore}
          onChange={(e) =>
            updateParam("min_score", e.target.value || null)
          }
          className="w-20 rounded-md border border-gray-300 bg-white px-2 py-1 text-xs dark:border-gray-700 dark:bg-gray-900"
        />
      </div>
    </div>
  );
}

function ToggleGroup({
  label,
  options,
  active,
  onChange,
}: {
  label: string;
  options: { value: string; label: string }[];
  active: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
        {label}
      </span>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={cn(
            "rounded-md border px-2.5 py-1 text-xs transition",
            opt.value === active
              ? "border-blue-300 bg-blue-50 text-blue-800 dark:border-blue-700 dark:bg-blue-900 dark:text-blue-100"
              : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300",
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
