import React, { useState, useCallback } from 'react'
import { Check, Copy } from 'lucide-react'

interface CodeBlockProps {
  code: string
  language?: string
  filename?: string
  showLineNumbers?: boolean
  className?: string
}

const LANGUAGE_NAMES: Record<string, string> = {
  js: 'JavaScript', jsx: 'JSX', ts: 'TypeScript', tsx: 'TSX',
  py: 'Python', python: 'Python', rb: 'Ruby', java: 'Java',
  go: 'Go', rust: 'Rust', rs: 'Rust', c: 'C', cpp: 'C++',
  json: 'JSON', yaml: 'YAML', yml: 'YAML', xml: 'XML',
  html: 'HTML', css: 'CSS', sh: 'Shell', bash: 'Bash', sql: 'SQL',
}

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] || c))
}

function highlightCode(code: string, language?: string): string {
  if (!language) return escapeHtml(code)
  
  let result = escapeHtml(code)
  
  // Minimal syntax highlighting
  const patterns: [RegExp, string][] = [
    [/(&quot;.*?&quot;|&#39;.*?&#39;|`[^`]*`)/g, '<span class="text-emerald-400">$1</span>'],
    [/(\/\/.*$|#.*$)/gm, '<span class="text-zinc-600">$1</span>'],
    [/(\/\*[\s\S]*?\*\/)/g, '<span class="text-zinc-600">$1</span>'],
    [/\b(const|let|var|function|class|return|if|else|for|while|import|from|export|default|async|await|def|self|True|False|None)\b/g, '<span class="text-violet-400">$1</span>'],
    [/\b(\d+\.?\d*)\b/g, '<span class="text-amber-400">$1</span>'],
  ]
  
  patterns.forEach(([pattern, replacement]) => {
    result = result.replace(pattern, replacement)
  })
  
  return result
}

/**
 * Minimal CodeBlock with copy button.
 */
export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language,
  filename,
  showLineNumbers = false,
  className = '',
}) => {
  const [copied, setCopied] = useState(false)
  
  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }, [code])

  const lines = code.split('\n')
  const lang = language ? LANGUAGE_NAMES[language.toLowerCase()] || language : null

  return (
    <div className={`group relative rounded-lg overflow-hidden bg-zinc-900 border border-zinc-800 my-2 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-2 text-[11px] text-zinc-500">
          {filename && <span className="text-zinc-400">{filename}</span>}
          {lang && <span>{lang}</span>}
        </div>
        
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {copied ? (
            <>
              <Check size={12} />
              <span>Copied</span>
            </>
          ) : (
            <>
              <Copy size={12} />
              <span className="hidden group-hover:inline">Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code */}
      <div className="overflow-x-auto">
        <pre className="p-3 text-xs font-mono leading-relaxed">
          <code className="text-zinc-300">
            {lines.map((line, i) => (
              <div key={i} className="table-row">
                {showLineNumbers && (
                  <span className="table-cell pr-3 text-zinc-600 select-none text-right w-6">
                    {i + 1}
                  </span>
                )}
                <span
                  className="table-cell"
                  dangerouslySetInnerHTML={{ __html: highlightCode(line, language) }}
                />
              </div>
            ))}
          </code>
        </pre>
      </div>
    </div>
  )
}

export const InlineCode: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <code className="px-1 py-0.5 rounded bg-zinc-800 text-zinc-300 text-xs font-mono">
    {children}
  </code>
)

export default CodeBlock
