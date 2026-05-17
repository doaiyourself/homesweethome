import Link from "next/link";

import { ArticleCard } from "@/components/ArticleCard";
import { ArticleFilters } from "@/components/ArticleFilters";
import { api } from "@/lib/api";
import type { ArticleListQuery } from "@/lib/types";

export const dynamic = "force-dynamic";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function parseQuery(sp: Record<string, string | string[] | undefined>): ArticleListQuery {
  const get = (k: string) => (Array.isArray(sp[k]) ? (sp[k] as string[])[0] : sp[k]) as string | undefined;
  const getAll = (k: string) =>
    Array.isArray(sp[k]) ? (sp[k] as string[]) : sp[k] ? [sp[k] as string] : undefined;
  return {
    status: (get("status") as ArticleListQuery["status"]) ?? "active",
    sort: (get("sort") as ArticleListQuery["sort"]) ?? "score",
    min_score: get("min_score") ? Number(get("min_score")) : undefined,
    trade_type: getAll("trade_type"),
    real_estate_type: getAll("real_estate_type"),
    cortar_no: get("cortar_no"),
    page: get("page") ? Number(get("page")) : 1,
    page_size: 20,
    show_hidden: get("show_hidden") === "true",
  };
}

export default async function ArticlesPage(props: { searchParams: SearchParams }) {
  const sp = await props.searchParams;
  const query = parseQuery(sp);
  const result = await api.listArticles(query).catch((e: Error) => ({
    error: e.message,
    items: [],
    total: 0,
    page: 1,
    page_size: 20,
  }));

  const page = query.page ?? 1;
  const totalPages = Math.max(1, Math.ceil(result.total / (query.page_size ?? 20)));

  const buildPageHref = (p: number) => {
    const next = new URLSearchParams();
    for (const [k, v] of Object.entries(sp)) {
      if (v === undefined) continue;
      if (Array.isArray(v)) v.forEach((vv) => next.append(k, vv));
      else next.set(k, v);
    }
    next.set("page", String(p));
    return `/articles?${next.toString()}`;
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">매물</h1>

      <ArticleFilters />

      <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
        <span>총 {result.total.toLocaleString()}건</span>
        <span>
          {page} / {totalPages}페이지
        </span>
      </div>

      {result.items.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400">
          조건에 맞는 매물이 없습니다.
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {result.items.map((a) => (
            <ArticleCard key={a.article_no} article={a} />
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
          {page > 1 && (
            <Link
              href={buildPageHref(page - 1)}
              className="rounded-md border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:hover:bg-gray-800"
            >
              이전
            </Link>
          )}
          {page < totalPages && (
            <Link
              href={buildPageHref(page + 1)}
              className="rounded-md border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:hover:bg-gray-800"
            >
              다음
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
