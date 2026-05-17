"use server";

import { revalidatePath } from "next/cache";

import { api } from "@/lib/api";
import type { UserPref } from "@/lib/types";

export async function savePrefs(patch: Partial<UserPref>): Promise<UserPref> {
  const updated = await api.updatePrefs(patch);
  revalidatePath("/settings");
  revalidatePath("/articles");
  revalidatePath("/");
  return updated;
}
