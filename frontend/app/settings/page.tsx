import { SettingsForm } from "./SettingsForm";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  const prefs = await api.getPrefs();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">설정</h1>
      <p className="text-sm text-gray-600 dark:text-gray-400">
        검색 조건과 점수 가중치를 조정하세요. 변경사항은 다음 크롤부터
        반영됩니다.
      </p>
      <SettingsForm initial={prefs} />
    </div>
  );
}
