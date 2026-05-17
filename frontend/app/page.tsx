import Link from "next/link";

import { ArticleCard } from "@/components/ArticleCard";
import { StatsHeader } from "@/components/StatsHeader";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  // Fetch in parallel
  const [stats, top, recent] = await Promise.allSettled([
    api.getStats(),
    api.listArticles({ status: "active", sort: "score", page_size: 6 }),
    api.listArticles({ status: "new", sort: "date", page_size: 6 }),
  ]);

  if (
    stats.status === "rejected" ||
    top.status === "rejected" ||
    recent.status === "rejected"
  ) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
        백엔드 API 호출에 실패했습니다. <code>NEXT_PUBLIC_API_BASE_URL</code>이
        올바르게 설정되었고 백엔드가 실행 중인지 확인해주세요.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <StatsHeader stats={stats.value} />

      <Section title="🌟 오늘의 추천" link="/articles">
        {top.value.items.length === 0 ? (
          <Empty message="아직 매물이 없습니다. 백엔드에서 크롤링을 한 번 실행해주세요." />
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {top.value.items.map((a) => (
              <ArticleCard key={a.article_no} article={a} />
            ))}
          </div>
        )}
      </Section>

      <Section
        title="🆕 24시간 내 신규"
        link="/articles?status=new&sort=date"
      >
        {recent.value.items.length === 0 ? (
          <Empty message="최근 24시간 동안 신규 매물이 없습니다." />
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {recent.value.items.map((a) => (
              <ArticleCard key={a.article_no} article={a} />
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

function Section({
  title,
  link,
  children,
}: {
  title: string;
  link?: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">{title}</h2>
        {link && (
          <Link
            href={link}
            className="text-xs text-blue-600 hover:underline dark:text-blue-400"
          >
            전체보기 →
          </Link>
        )}
      </div>
      {children}
    </section>
  );
}

function Empty({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-dashed border-gray-300 bg-white p-6 text-center text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400">
      {message}
    </div>
  );
}
