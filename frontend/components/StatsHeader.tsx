import type { Stats } from "@/lib/types";

type Props = {
  stats: Stats;
};

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
      <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold text-gray-900 dark:text-gray-100">
        {value}
      </div>
      {hint && (
        <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          {hint}
        </div>
      )}
    </div>
  );
}

export function StatsHeader({ stats }: Props) {
  const last = stats.last_crawl_at
    ? new Date(stats.last_crawl_at).toLocaleString("ko-KR", {
        timeZone: "Asia/Seoul",
      })
    : "—";
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <StatCard label="활성 매물" value={stats.active_count.toLocaleString()} />
      <StatCard
        label="24h 신규"
        value={stats.new_today_count.toLocaleString()}
      />
      <StatCard
        label="평균 점수"
        value={
          stats.avg_score_active !== null
            ? stats.avg_score_active.toFixed(1)
            : "—"
        }
      />
      <StatCard label="마지막 크롤" value={last} hint="KST" />
    </div>
  );
}
