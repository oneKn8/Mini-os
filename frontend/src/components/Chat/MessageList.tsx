import type { ChatMessage } from '../../types/chat'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import TypewriterText from './TypewriterText'
import { CodeBlock } from './CodeBlock'
import { useChatStore } from '../../store/chatStore'

interface MessageListProps {
  messages: ChatMessage[]
}

export default function MessageList({ messages }: MessageListProps) {
  const { isStreaming } = useChatStore()

  return (
    <div className="flex flex-col space-y-3">
      {messages.map((msg, idx) => {
        const isUser = msg.sender === 'user'
        const isLatestAssistant = !isUser && idx === messages.length - 1
        const shouldAnimate = isLatestAssistant && !isStreaming

        return (
          <div
            key={msg.id || idx}
            className={isUser ? "flex justify-end" : "flex justify-start"}
          >
            <div
              className={
                isUser
                  ? "max-w-[85%] px-3 py-2 rounded-2xl rounded-br-md bg-zinc-800 text-zinc-100 text-sm"
                  : "w-full text-zinc-300 text-sm leading-relaxed"
              }
            >
              {isUser ? (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              ) : shouldAnimate ? (
                <TypewriterText text={msg.content} speed={80} />
              ) : (
                <div className="prose prose-sm prose-invert max-w-none prose-zinc">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: (props) => <h1 className="text-xl font-semibold text-zinc-100 mb-3 mt-4" {...props} />,
                      h2: (props) => <h2 className="text-lg font-semibold text-zinc-100 mb-2 mt-3" {...props} />,
                      h3: (props) => <h3 className="text-base font-medium text-zinc-200 mb-2 mt-3" {...props} />,
                      p: (props) => <p className="mb-2 text-zinc-300 leading-relaxed" {...props} />,
                      ul: (props) => <ul className="list-disc pl-5 mb-2 space-y-1 text-zinc-300" {...props} />,
                      ol: (props) => <ol className="list-decimal pl-5 mb-2 space-y-1 text-zinc-300" {...props} />,
                      li: (props) => <li className="text-zinc-300" {...props} />,
                      strong: (props) => <strong className="font-medium text-zinc-100" {...props} />,
                      em: (props) => <em className="italic text-zinc-400" {...props} />,
                      code: ({ className, children, ...props }: any) => {
                        const match = /language-(\w+)/.exec(className || '')
                        const language = match ? match[1] : undefined
                        const codeString = String(children).replace(/\n$/, '')
                        const isInline = !className
                        
                        if (isInline) {
                          return (
                            <code className="px-1 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono text-xs" {...props}>
                              {children}
                            </code>
                          )
                        }
                        
                        return <CodeBlock code={codeString} language={language} showLineNumbers={codeString.split('\n').length > 3} />
                      },
                      pre: ({ children }) => <>{children}</>,
                      blockquote: (props) => <blockquote className="border-l-2 border-zinc-700 pl-3 text-zinc-400 italic my-2" {...props} />,
                      a: (props) => <a className="text-zinc-400 hover:text-zinc-200 underline underline-offset-2" target="_blank" rel="noopener noreferrer" {...props} />,
                      hr: () => <hr className="border-zinc-800 my-3" />,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
