// Mirrors the Pydantic schemas in backend/app/schemas/*.

export type TradeType = "B1" | "B2" | "A1" | "B3";
export type RealEstateType = "APT" | "OPST" | "VL";

export type Article = {
  article_no: string;
  complex_name: string | null;
  building_name: string | null;
  trade_type: TradeType | null;
  trade_type_name: string | null;
  real_estate_type: RealEstateType | null;
  real_estate_type_name: string | null;
  deposit: number | null;
  monthly_rent: number | null;
  price_display: string | null;
  area1_sqm: number | null;
  area2_sqm: number | null;
  area_pyeong: number | null;
  floor_current: string | null;
  floor_total: number | null;
  direction: string | null;
  description: string | null;
  tags: string[];
  latitude: number | null;
  longitude: number | null;
  cortar_no: string | null;
  address_text: string | null;
  image_url: string | null;
  cp_name: string | null;
  cp_article_url: string | null;
  article_status: string | null;
  verification_type: string | null;
  article_confirm_ymd: string | null;
  first_seen_at: string;
  last_seen_at: string;
  is_active: boolean;
  score: number | null;
  is_favorited: boolean;
  is_hidden: boolean;
};

export type ArticleListResponse = {
  items: Article[];
  total: number;
  page: number;
  page_size: number;
};

export type UserPref = {
  id: number;
  label: string;
  region_codes: string[];
  trade_types: string[];
  real_estate_types: string[];
  deposit_min: number | null;
  deposit_max: number | null;
  monthly_rent_max: number | null;
  area_min_pyeong: number | null;
  area_max_pyeong: number | null;
  floor_min: number | null;
  must_have_keywords: string[];
  exclude_keywords: string[];
  weights: Record<string, number>;
};

export type Stats = {
  active_count: number;
  new_today_count: number;
  avg_score_active: number | null;
  last_crawl_at: string | null;
};

export type ArticleListQuery = {
  status?: "active" | "new" | "all";
  min_score?: number;
  cortar_no?: string;
  trade_type?: string[];
  real_estate_type?: string[];
  sort?: "score" | "date" | "last_seen";
  page?: number;
  page_size?: number;
  show_hidden?: boolean;
};
