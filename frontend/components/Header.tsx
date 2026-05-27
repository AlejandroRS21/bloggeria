import Link from "next/link";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-200/80 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link href="/" className="group flex items-center gap-2">
          <span className="text-2xl font-extrabold tracking-tight text-gray-900 transition-colors group-hover:text-blue-600">
            BLOGGER<span className="text-blue-600">IA</span>
          </span>
        </Link>

        <nav className="flex items-center gap-5">
          <Link
            href="/"
            className="text-sm font-medium text-gray-600 transition-colors hover:text-blue-600"
          >
            Blog
          </Link>
          <Link
            href="/tags"
            className="text-sm font-medium text-gray-600 transition-colors hover:text-blue-600"
          >
            Tags
          </Link>
          <Link
            href="/archive"
            className="text-sm font-medium text-gray-600 transition-colors hover:text-blue-600"
          >
            Archivo
          </Link>
          <Link
            href="/project"
            className="hidden text-sm font-medium text-gray-600 transition-colors hover:text-blue-600 sm:inline"
          >
            Proyecto
          </Link>

          <a
            href="https://github.com/AlejandroRS21/blogger-agent-tfg"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden text-sm font-medium text-gray-600 transition-colors hover:text-blue-600 sm:inline"
          >
            GitHub
          </a>
          <Link
            href="/posts/new"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700"
          >
            Generar
          </Link>
        </nav>
      </div>
    </header>
  );
}
