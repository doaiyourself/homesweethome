// Thin wrapper around fetch with the backend base URL baked in.

import type {
  Article,
  ArticleListQuery,
  ArticleListResponse,
  Stats,
  UserPref,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const resp = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    cache: init.cache ?? "no-store",
  });
  if (!resp.ok) {
    let detail = `${resp.status}`;
    try {
      const body = await resp.json();
      detail = body.detail ?? detail;
    } catch {
      /* no body */
    }
    throw new ApiError(resp.status, detail);
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

function toQuery(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      for (const v of value) search.append(key, String(v));
    } else if (typeof value === "boolean") {
      search.set(key, value ? "true" : "false");
    } else {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const api = {
  listArticles(query: ArticleListQuery = {}): Promise<ArticleListResponse> {
    return request(`/api/articles${toQuery(query)}`);
  },
  getArticle(articleNo: string): Promise<Article> {
    return request(`/api/articles/${articleNo}`);
  },
  listFavorites(
    page = 1,
    pageSize = 50,
  ): Promise<ArticleListResponse> {
    return request(`/api/articles/favorites${toQuery({ page, page_size: pageSize })}`);
  },
  addFavorite(articleNo: string): Promise<void> {
    return request(`/api/articles/${articleNo}/favorite`, { method: "POST" });
  },
  removeFavorite(articleNo: string): Promise<void> {
    return request(`/api/articles/${articleNo}/favorite`, { method: "DELETE" });
  },
  addHide(articleNo: string): Promise<void> {
    return request(`/api/articles/${articleNo}/hide`, { method: "POST" });
  },
  removeHide(articleNo: string): Promise<void> {
    return request(`/api/articles/${articleNo}/hide`, { method: "DELETE" });
  },
  getPrefs(): Promise<UserPref> {
    return request(`/api/prefs`);
  },
  updatePrefs(body: Partial<UserPref>): Promise<UserPref> {
    return request(`/api/prefs`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },
  getStats(): Promise<Stats> {
    return request(`/api/stats`);
  },
};

export { ApiError };
