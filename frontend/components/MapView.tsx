"use client";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import Link from "next/link";

import { ScoreBadge } from "@/components/ScoreBadge";
import type { Article } from "@/lib/types";
import { TRADE_LABELS, formatPrice } from "@/lib/utils";

// Default Leaflet marker icons reference /static paths that Next.js doesn't
// serve. Rebind to CDN URLs so markers render without a custom build step.
// (Done at module init; cheap and idempotent.)
delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: () => string })
  ._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:
    "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:
    "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-shadow.png",
});

type Props = {
  articles: Article[];
  focusArticleNo?: string;
};

const SEOUL_CENTER: [number, number] = [37.5, 126.88]; // around Guro

function FlyTo({ position }: { position: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (position) map.flyTo(position, 17, { duration: 0.7 });
  }, [map, position]);
  return null;
}

export default function MapView({ articles, focusArticleNo }: Props) {
  const focusPos = useMemo<[number, number] | null>(() => {
    if (!focusArticleNo) return null;
    const a = articles.find((x) => x.article_no === focusArticleNo);
    return a && a.latitude && a.longitude ? [a.latitude, a.longitude] : null;
  }, [articles, focusArticleNo]);

  const center: [number, number] = focusPos ?? SEOUL_CENTER;

  return (
    <div className="h-[70vh] w-full overflow-hidden rounded-lg border border-gray-200 dark:border-gray-800">
      <MapContainer
        center={center}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FlyTo position={focusPos} />
        {articles
          .filter((a) => a.latitude && a.longitude)
          .map((a) => (
            <Marker
              key={a.article_no}
              position={[a.latitude as number, a.longitude as number]}
            >
              <Popup>
                <div className="space-y-1">
                  <div className="font-semibold">
                    {a.complex_name ?? a.article_no}
                  </div>
                  <div className="text-xs text-gray-600">
                    {TRADE_LABELS[a.trade_type ?? ""] ?? ""}{" "}
                    {formatPrice(
                      a.trade_type,
                      a.deposit,
                      a.monthly_rent,
                      a.price_display,
                    )}
                  </div>
                  <div>
                    <ScoreBadge score={a.score} />
                  </div>
                  <Link
                    href={`/articles/${a.article_no}`}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    상세 →
                  </Link>
                </div>
              </Popup>
            </Marker>
          ))}
      </MapContainer>
    </div>
  );
}
