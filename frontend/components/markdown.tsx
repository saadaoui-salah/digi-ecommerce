"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Renders store descriptions written in Markdown with the site's own styles,
 * so no extra typography plugin is needed.
 */
export function Markdown({
  content,
  className = "",
}: {
  content: string;
  className?: string;
}) {
  return (
    <div className={`markdown ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
          h1: ({ children }) => (
            <h1 className="mb-3 text-lg font-semibold text-foreground">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="mb-3 text-base font-semibold text-foreground">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-2 text-sm font-semibold text-foreground">{children}</h3>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">{children}</strong>
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sky-700 underline underline-offset-2 hover:text-sky-600 dark:text-sky-300 dark:hover:text-sky-200"
            >
              {children}
            </a>
          ),
          ul: ({ children }) => (
            <ul className="mb-3 list-disc ps-5 last:mb-0">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-3 list-decimal ps-5 last:mb-0">{children}</ol>
          ),
          li: ({ children }) => <li className="mb-1 last:mb-0">{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className="mb-3 border-s-2 border-border ps-3 italic last:mb-0">
              {children}
            </blockquote>
          ),
          code: ({ children }) => (
            <code className="rounded bg-surface-muted px-1 py-0.5 font-mono text-xs">
              {children}
            </code>
          ),
          pre: ({ children }) => (
            <pre className="mb-3 overflow-x-auto rounded-lg bg-surface-muted p-3 last:mb-0">
              {children}
            </pre>
          ),
          table: ({ children }) => (
            <div className="mb-3 overflow-x-auto">
              <table className="w-full border-collapse text-start">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-border px-2 py-1 text-start font-semibold">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-border px-2 py-1">{children}</td>
          ),
          hr: () => <hr className="my-4 border-border" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
