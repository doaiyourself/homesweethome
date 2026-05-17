import Link from "next/link";

const NAV = [
  { href: "/", label: "홈" },
  { href: "/articles", label: "매물" },
  { href: "/favorites", label: "찜" },
  { href: "/map", label: "지도" },
  { href: "/settings", label: "설정" },
];

export function Header() {
  return (
    <header className="sticky top-0 z-30 border-b border-gray-200 bg-white/90 backdrop-blur dark:border-gray-800 dark:bg-gray-950/90">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link
          href="/"
          className="text-base font-semibold tracking-tight text-gray-900 dark:text-gray-100"
        >
          🏠 신혼집
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-2.5 py-1.5 text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
