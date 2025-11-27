import { MessageCircle, X } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'
import ChatWindow from './ChatWindow'

export default function ChatWidget() {
  const { isOpen, toggleChat } = useChatStore()

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end font-sans">
      {isOpen && (
        <div className="mb-3 h-[600px] w-[400px] overflow-hidden rounded-xl bg-zinc-950 border border-zinc-800 shadow-2xl">
          <ChatWindow />
        </div>
      )}

      <button
        onClick={toggleChat}
        className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-800 text-zinc-300 shadow-lg hover:bg-zinc-700 hover:text-zinc-100 transition-colors border border-zinc-700"
      >
        {isOpen ? <X size={20} /> : <MessageCircle size={20} />}
      </button>
    </div>
  )
}
