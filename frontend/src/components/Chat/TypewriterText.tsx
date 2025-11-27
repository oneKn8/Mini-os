import React, { useEffect, useState, useRef } from 'react'
import ReactMarkdown from 'react-markdown'

interface TypewriterTextProps {
  text: string
  speed?: number
  onComplete?: () => void
  className?: string
  skipAnimation?: boolean
  renderMarkdown?: boolean
}

/**
 * TypewriterText - clean, minimal text streaming without layout shifts.
 */
export const TypewriterText: React.FC<TypewriterTextProps> = ({
  text,
  speed = 60,
  onComplete,
  className = '',
  skipAnimation = false,
  renderMarkdown = true,
}) => {
  const [displayedText, setDisplayedText] = useState(skipAnimation ? text : '')
  const [isComplete, setIsComplete] = useState(skipAnimation)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const prevTextRef = useRef(text)

  useEffect(() => {
    // If text changed, reset
    if (text !== prevTextRef.current) {
      prevTextRef.current = text
      if (skipAnimation) {
        setDisplayedText(text)
        setIsComplete(true)
        return
      }
      setDisplayedText('')
      setIsComplete(false)
    }
  }, [text, skipAnimation])

  useEffect(() => {
    if (skipAnimation || isComplete) return

    let idx = displayedText.length
    const delay = 1000 / speed

    intervalRef.current = setInterval(() => {
      if (idx < text.length) {
        const chunk = speed > 80 ? 4 : speed > 40 ? 2 : 1
        idx = Math.min(idx + chunk, text.length)
        setDisplayedText(text.slice(0, idx))
      } else {
        clearInterval(intervalRef.current!)
        setIsComplete(true)
        onComplete?.()
      }
    }, delay)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [text, speed, skipAnimation, isComplete, onComplete, displayedText.length])

  const content = renderMarkdown ? (
    <ReactMarkdown
      components={{
        code: ({ className: codeClass, children, ...props }) => {
          const isInline = !codeClass
          return isInline ? (
            <code className="px-1 py-0.5 rounded bg-zinc-800 text-zinc-300 text-sm font-mono" {...props}>
              {children}
            </code>
          ) : (
            <code className={codeClass} {...props}>{children}</code>
          )
        },
        pre: ({ children }) => (
          <pre className="bg-zinc-900 rounded-lg p-3 overflow-x-auto my-2 text-sm">{children}</pre>
        ),
        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
        ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
        li: ({ children }) => <li>{children}</li>,
        strong: ({ children }) => <strong className="font-medium text-white">{children}</strong>,
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer" className="text-zinc-400 hover:text-white underline underline-offset-2">
            {children}
          </a>
        ),
      }}
    >
      {displayedText}
    </ReactMarkdown>
  ) : (
    <span>{displayedText}</span>
  )

  return (
    <div className={className}>
      {content}
      {!isComplete && <span className="inline-block w-1.5 h-4 bg-zinc-500 ml-0.5 animate-pulse" />}
    </div>
  )
}

export const StreamingText: React.FC<{
  text: string
  isStreaming: boolean
  className?: string
  renderMarkdown?: boolean
}> = ({ text, isStreaming, className = '', renderMarkdown = true }) => (
  <div className={className}>
    {renderMarkdown ? <ReactMarkdown>{text}</ReactMarkdown> : <span>{text}</span>}
    {isStreaming && <span className="inline-block w-1.5 h-4 bg-zinc-500 ml-0.5 animate-pulse" />}
  </div>
)

export default TypewriterText
