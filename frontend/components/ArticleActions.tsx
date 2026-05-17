"use client";

import { useTransition } from "react";
import { Heart, EyeOff } from "lucide-react";
import { useRouter } from "next/navigation";

import { toggleFavorite, toggleHide } from "@/app/articles/actions";
import { cn } from "@/lib/utils";

type Props = {
  articleNo: string;
  isFavorited: boolean;
  isHidden: boolean;
  className?: string;
};

export function ArticleActions({
  articleNo,
  isFavorited,
  isHidden,
  className,
}: Props) {
  const [pending, start] = useTransition();
  const router = useRouter();

  const onToggle = (kind: "favorite" | "hide", current: boolean) => {
    start(async () => {
      if (kind === "favorite") await toggleFavorite(articleNo, current);
      else await toggleHide(articleNo, current);
      router.refresh();
    });
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <button
        type="button"
        onClick={() => onToggle("favorite", isFavorited)}
        disabled={pending}
        title={isFavorited ? "찜 해제" : "찜"}
        className={cn(
          "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs transition",
          isFavorited
            ? "border-pink-300 bg-pink-50 text-pink-700 dark:border-pink-700 dark:bg-pink-950 dark:text-pink-200"
            : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300",
          pending && "opacity-50",
        )}
      >
        <Heart
          size={14}
          className={isFavorited ? "fill-current" : ""}
        />
        {isFavorited ? "찜됨" : "찜"}
      </button>
      <button
        type="button"
        onClick={() => onToggle("hide", isHidden)}
        disabled={pending}
        title={isHidden ? "숨김 해제" : "숨기기"}
        className={cn(
          "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs transition",
          isHidden
            ? "border-gray-400 bg-gray-100 text-gray-800 dark:border-gray-500 dark:bg-gray-800 dark:text-gray-100"
            : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300",
          pending && "opacity-50",
        )}
      >
        <EyeOff size={14} />
        {isHidden ? "숨김됨" : "숨기기"}
      </button>
    </div>
  );
}
