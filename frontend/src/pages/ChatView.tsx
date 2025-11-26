import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChatStore } from '../store/chatStore'

function ChatView() {
  const navigate = useNavigate()
  const { setOpen } = useChatStore()

  useEffect(() => {
    // Redirect to home and open the chat widget
    setOpen(true)
    navigate('/today', { replace: true })
  }, [navigate, setOpen])

  return null
}

export default ChatView
