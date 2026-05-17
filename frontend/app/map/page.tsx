import nextDynamic from "next/dynamic";

import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

// Leaflet touches `window` at import-time, so dynamic-import with SSR off.
const MapView = nextDynamic(() => import("@/components/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[70vh] items-center justify-center rounded-lg border border-gray-200 bg-white text-sm text-gray-500 dark:border-gray-800 dark:bg-gray-900">
      지도 로딩 중...
    </div>
  ),
});

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default async function MapPage(props: { searchParams: SearchParams }) {
  const sp = await props.searchParams;
  const focus = typeof sp.focus === "string" ? sp.focus : undefined;
  // Pull a generous page so the map shows everything the user might pan to.
  const result = await api.listArticles({
    status: "active",
    sort: "score",
    page_size: 200,
  });
  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">지도</h1>
      <div className="text-sm text-gray-600 dark:text-gray-400">
        {result.total.toLocaleString()}건 중 좌표 있는 {result.items.filter((a) => a.latitude && a.longitude).length}건 표시
      </div>
      <MapView articles={result.items} focusArticleNo={focus} />
    </div>
  );
}
