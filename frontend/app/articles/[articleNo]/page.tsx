import Link from "next/link";
import { notFound } from "next/navigation";

import { ArticleActions } from "@/components/ArticleActions";
import { ScoreBadge } from "@/components/ScoreBadge";
import { api } from "@/lib/api";
import { ApiError } from "@/lib/api";
import { TRADE_LABELS, formatPrice } from "@/lib/utils";

export const dynamic = "force-dynamic";

type Params = Promise<{ articleNo: string }>;

export default async function ArticleDetailPage(props: { params: Params }) {
  const { articleNo } = await props.params;
  let article;
  try {
    article = await api.getArticle(articleNo);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }

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
      : article.floor_current;

  return (
    <div className="space-y-5">
      <Link
        href="/articles"
        className="text-sm text-blue-600 hover:underline dark:text-blue-400"
      >
        ← 매물 목록으로
      </Link>

      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        {article.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={article.image_url}
            alt={article.complex_name ?? ""}
            className="h-64 w-full object-cover"
          />
        ) : (
          <div className="flex h-48 w-full items-center justify-center bg-gray-100 text-5xl text-gray-300 dark:bg-gray-800">
            🏠
          </div>
        )}
        <div className="space-y-3 p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {article.complex_name ?? article.building_name ?? article.article_no}
              </h1>
              <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {[article.real_estate_type_name, tradeLabel, article.direction]
                  .filter(Boolean)
                  .join(" · ")}
              </div>
            </div>
            <ScoreBadge score={article.score} className="text-sm" />
          </div>

          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <Row label="가격">{price}</Row>
            <Row label="면적">
              {article.area_pyeong ? `${article.area_pyeong}평` : "—"}
              {article.area2_sqm
                ? ` (전용 ${article.area2_sqm.toFixed(1)}㎡)`
                : ""}
            </Row>
            <Row label="층">{floor ?? "—"}</Row>
            <Row label="향">{article.direction ?? "—"}</Row>
            <Row label="확인일">
              {article.article_confirm_ymd
                ? `${article.article_confirm_ymd.slice(0, 4)}-${article.article_confirm_ymd.slice(4, 6)}-${article.article_confirm_ymd.slice(6, 8)}`
                : "—"}
            </Row>
            <Row label="중개">{article.cp_name ?? "—"}</Row>
          </dl>

          {article.description && (
            <div className="rounded-md bg-gray-50 p-3 text-sm text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              {article.description}
            </div>
          )}

          {article.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {article.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between pt-1">
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
                className="text-sm text-blue-600 hover:underline dark:text-blue-400"
              >
                네이버 원문 보기 ↗
              </a>
            )}
          </div>
        </div>
      </div>

      {article.latitude && article.longitude && (
        <div className="rounded-lg border border-gray-200 bg-white p-4 text-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="mb-1 font-medium text-gray-900 dark:text-gray-100">
            위치
          </div>
          <a
            href={`https://map.naver.com/v5/?lng=${article.longitude}&lat=${article.latitude}&zoom=17`}
            target="_blank"
            rel="noreferrer"
            className="text-blue-600 hover:underline dark:text-blue-400"
          >
            네이버 지도에서 보기 ↗
          </a>
          <Link
            href={`/map?focus=${article.article_no}`}
            className="ml-3 text-blue-600 hover:underline dark:text-blue-400"
          >
            매물 지도에서 보기 ↗
          </Link>
        </div>
      )}
    </div>
  );
}

function Row({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
        {label}
      </dt>
      <dd className="text-gray-900 dark:text-gray-100">{children}</dd>
    </div>
  );
}
