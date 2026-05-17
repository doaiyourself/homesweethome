import Link from "next/link";

import { ArticleActions } from "@/components/ArticleActions";
import { ScoreBadge } from "@/components/ScoreBadge";
import type { Article } from "@/lib/types";
import { TRADE_LABELS, cn, formatPrice } from "@/lib/utils";

type Props = {
  article: Article;
};

export function ArticleCard({ article }: Props) {
  const tradeLabel =
    TRADE_LABELS[article.trade_type ?? ""] ?? article.trade_type ?? "";
  const price = formatPrice(
    article.trade_type,
    article.deposit,
    article.monthly_rent,
    article.price_display,
  );

  const floor =
    article.floor_current && article.floor_total
      ? `${article.floor_current}/${article.floor_total}층`
      : article.floor_current
      ? `${article.floor_current}층`
      : null;

  return (
    <article className="flex gap-3 rounded-lg border border-gray-200 bg-white p-4 transition hover:shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <div className="hidden h-24 w-24 flex-shrink-0 overflow-hidden rounded-md bg-gray-100 sm:block dark:bg-gray-800">
        {article.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={article.image_url}
            alt={article.complex_name ?? ""}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-2xl text-gray-300">
            🏠
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <Link
              href={`/articles/${article.article_no}`}
              className="block truncate text-sm font-semibold text-gray-900 hover:underline dark:text-gray-100"
            >
              {article.complex_name ?? article.building_name ?? article.article_no}
            </Link>
            <div className="mt-0.5 truncate text-xs text-gray-500 dark:text-gray-400">
              {[article.real_estate_type_name, tradeLabel, article.direction]
                .filter(Boolean)
                .join(" · ")}
            </div>
          </div>
          <ScoreBadge score={article.score} />
        </div>

        <div className="mt-1 flex flex-wrap items-baseline gap-x-3 gap-y-1 text-sm text-gray-700 dark:text-gray-300">
          <span className="font-medium">{price}</span>
          {article.area_pyeong && <span>{article.area_pyeong}평</span>}
          {floor && <span>{floor}</span>}
        </div>

        {article.tags && article.tags.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {article.tags.slice(0, 4).map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-gray-700 dark:bg-gray-800 dark:text-gray-300"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        <div className="mt-2 flex items-center justify-between gap-2">
          <ArticleActions
            articleNo={article.article_no}
            isFavorited={article.is_favorited}
            isHidden={article.is_hidden}
          />
          {article.cp_article_url && (
            <a
              href={article.cp_article_url}
              target="_blank"
              rel="noreferrer"
              className={cn(
                "text-xs text-gray-500 hover:underline dark:text-gray-400",
              )}
            >
              네이버 원문 ↗
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
