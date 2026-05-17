import { cn } from "@/lib/utils";

type Props = {
  score: number | null;
  className?: string;
};

export function ScoreBadge({ score, className }: Props) {
  if (score === null) {
    return (
      <span
        className={cn(
          "inline-flex items-center rounded-full bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300",
          className,
        )}
      >
        점수 없음
      </span>
    );
  }
  const tone =
    score >= 90
      ? "bg-yellow-100 text-yellow-900 dark:bg-yellow-900/40 dark:text-yellow-200"
      : score >= 80
      ? "bg-green-100 text-green-900 dark:bg-green-900/40 dark:text-green-200"
      : score >= 70
      ? "bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-200"
      : "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-200";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
        tone,
        className,
      )}
      title={`점수 ${score.toFixed(1)}/100`}
    >
      ⭐ {score.toFixed(0)}
    </span>
  );
}
