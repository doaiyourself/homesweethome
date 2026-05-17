import { ArticleCard } from "@/components/ArticleCard";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function FavoritesPage() {
  const result = await api.listFavorites(1, 100);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">찜한 매물</h1>
      <div className="text-sm text-gray-600 dark:text-gray-400">
        총 {result.total}건
      </div>
      {result.items.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400">
          아직 찜한 매물이 없습니다. 매물 목록에서 ❤️ 버튼을 눌러 추가해보세요.
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {result.items.map((a) => (
            <ArticleCard key={a.article_no} article={a} />
          ))}
        </div>
      )}
    </div>
  );
}
