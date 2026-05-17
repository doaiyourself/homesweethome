"use server";

import { revalidatePath } from "next/cache";

import { api } from "@/lib/api";

export async function toggleFavorite(
  articleNo: string,
  isFavorited: boolean,
): Promise<void> {
  if (isFavorited) await api.removeFavorite(articleNo);
  else await api.addFavorite(articleNo);
  revalidatePath("/articles");
  revalidatePath(`/articles/${articleNo}`);
  revalidatePath("/favorites");
}

export async function toggleHide(
  articleNo: string,
  isHidden: boolean,
): Promise<void> {
  if (isHidden) await api.removeHide(articleNo);
  else await api.addHide(articleNo);
  revalidatePath("/articles");
  revalidatePath(`/articles/${articleNo}`);
}
