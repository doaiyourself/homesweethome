"use client";

import { useState, useTransition } from "react";

import { savePrefs } from "@/app/settings/actions";
import type { UserPref } from "@/lib/types";
import { cn } from "@/lib/utils";

const TRADE_OPTIONS = [
  { value: "A1", label: "매매" },
  { value: "B1", label: "전세" },
  { value: "B2", label: "월세" },
];
const REAL_ESTATE_OPTIONS = [
  { value: "APT", label: "아파트" },
  { value: "OPST", label: "오피스텔" },
  { value: "VL", label: "빌라" },
];
const REGION_OPTIONS = [
  { value: "1153000000", label: "구로구" },
  { value: "1147000000", label: "양천구" },
  { value: "1156000000", label: "영등포구" },
];
const WEIGHT_KEYS = [
  "price_fit",
  "area_fit",
  "floor_fit",
  "direction_score",
  "keyword_score",
  "freshness",
] as const;
const WEIGHT_LABELS: Record<string, string> = {
  price_fit: "가격 적합도",
  area_fit: "면적 적합도",
  floor_fit: "층 적합도",
  direction_score: "향",
  keyword_score: "키워드",
  freshness: "신선도",
};

type Props = {
  initial: UserPref;
};

export function SettingsForm({ initial }: Props) {
  const [form, setForm] = useState<UserPref>(initial);
  const [pending, start] = useTransition();
  const [saved, setSaved] = useState<string | null>(null);

  const update = <K extends keyof UserPref>(key: K, value: UserPref[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  const toggleArray = (key: "region_codes" | "trade_types" | "real_estate_types", v: string) => {
    setForm((f) => {
      const cur = new Set(f[key]);
      if (cur.has(v)) cur.delete(v);
      else cur.add(v);
      return { ...f, [key]: Array.from(cur) };
    });
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    start(async () => {
      await savePrefs(form);
      setSaved(new Date().toLocaleTimeString("ko-KR"));
    });
  };

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <Card title="지역">
        <CheckboxRow
          options={REGION_OPTIONS}
          values={form.region_codes}
          onToggle={(v) => toggleArray("region_codes", v)}
        />
      </Card>

      <Card title="거래 유형 / 매물 유형">
        <div className="space-y-3">
          <CheckboxRow
            label="거래"
            options={TRADE_OPTIONS}
            values={form.trade_types}
            onToggle={(v) => toggleArray("trade_types", v)}
          />
          <CheckboxRow
            label="유형"
            options={REAL_ESTATE_OPTIONS}
            values={form.real_estate_types}
            onToggle={(v) => toggleArray("real_estate_types", v)}
          />
        </div>
      </Card>

      <Card title="예산 (만원)">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          <NumberField
            label="보증금 최소"
            value={form.deposit_min}
            onChange={(v) => update("deposit_min", v)}
          />
          <NumberField
            label="보증금 최대"
            value={form.deposit_max}
            onChange={(v) => update("deposit_max", v)}
          />
          <NumberField
            label="월세 최대"
            value={form.monthly_rent_max}
            onChange={(v) => update("monthly_rent_max", v)}
          />
        </div>
      </Card>

      <Card title="면적 / 층">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          <NumberField
            label="최소 평수"
            value={form.area_min_pyeong}
            onChange={(v) => update("area_min_pyeong", v)}
            step={1}
          />
          <NumberField
            label="최대 평수"
            value={form.area_max_pyeong}
            onChange={(v) => update("area_max_pyeong", v)}
            step={1}
          />
          <NumberField
            label="최소 층"
            value={form.floor_min}
            onChange={(v) => update("floor_min", v)}
            step={1}
          />
        </div>
      </Card>

      <Card title="키워드">
        <div className="space-y-3">
          <KeywordField
            label="필수 키워드 (포함될수록 가점)"
            values={form.must_have_keywords}
            onChange={(v) => update("must_have_keywords", v)}
          />
          <KeywordField
            label="제외 키워드 (포함되면 큰 감점)"
            values={form.exclude_keywords}
            onChange={(v) => update("exclude_keywords", v)}
          />
        </div>
      </Card>

      <Card title="점수 가중치">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          {WEIGHT_KEYS.map((key) => (
            <NumberField
              key={key}
              label={WEIGHT_LABELS[key]}
              value={form.weights[key] ?? 0}
              onChange={(v) =>
                update("weights", { ...form.weights, [key]: v ?? 0 })
              }
              step={0.05}
            />
          ))}
        </div>
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          0~1 사이 값. 합이 1이 아니어도 자동 정규화됩니다.
        </p>
      </Card>

      <div className="flex items-center gap-3 pt-2">
        <button
          type="submit"
          disabled={pending}
          className={cn(
            "rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50",
          )}
        >
          {pending ? "저장 중..." : "저장"}
        </button>
        {saved && (
          <span className="text-xs text-green-700 dark:text-green-400">
            {saved}에 저장됨
          </span>
        )}
      </div>
    </form>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
      <h2 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
        {title}
      </h2>
      {children}
    </section>
  );
}

function CheckboxRow({
  label,
  options,
  values,
  onToggle,
}: {
  label?: string;
  options: { value: string; label: string }[];
  values: string[];
  onToggle: (v: string) => void;
}) {
  const set = new Set(values);
  return (
    <div className="flex flex-wrap items-center gap-2">
      {label && (
        <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
      )}
      {options.map((opt) => {
        const on = set.has(opt.value);
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onToggle(opt.value)}
            className={cn(
              "rounded-md border px-3 py-1 text-xs transition",
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
  );
}

function NumberField({
  label,
  value,
  onChange,
  step = 1,
}: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
  step?: number;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs">
      <span className="text-gray-500 dark:text-gray-400">{label}</span>
      <input
        type="number"
        value={value ?? ""}
        step={step}
        onChange={(e) =>
          onChange(e.target.value === "" ? null : Number(e.target.value))
        }
        className="rounded-md border border-gray-300 bg-white px-2 py-1 text-sm dark:border-gray-700 dark:bg-gray-900"
      />
    </label>
  );
}

function KeywordField({
  label,
  values,
  onChange,
}: {
  label: string;
  values: string[];
  onChange: (v: string[]) => void;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs">
      <span className="text-gray-500 dark:text-gray-400">{label}</span>
      <input
        type="text"
        value={values.join(", ")}
        onChange={(e) =>
          onChange(
            e.target.value
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean),
          )
        }
        placeholder="역세권, 신축, ..."
        className="rounded-md border border-gray-300 bg-white px-2 py-1 text-sm dark:border-gray-700 dark:bg-gray-900"
      />
    </label>
  );
}
