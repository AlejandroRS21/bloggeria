export default function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-slate-900">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="text-center sm:text-left">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Blogger Agent
            </p>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Desarrollado por <strong>Alejandro Ramírez Salado</strong> como Proyecto Académico
            </p>
          </div>

          <div className="flex items-center gap-4">
            <a
              href="https://github.com/AlejandroRS21/blogger-agent-tfg"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-gray-500 transition-colors hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
            >
              GitHub
            </a>
          </div>
        </div>

        <div className="mt-6 border-t border-gray-200 pt-4 text-center dark:border-gray-800">
          <p className="text-xs text-gray-400 dark:text-gray-500">
            &copy; {new Date().getFullYear()} Blogger Agent. Creado por Alejandro Ramírez Salado (@AlejandroRS21).
          </p>
        </div>
      </div>
    </footer>
  );
}
