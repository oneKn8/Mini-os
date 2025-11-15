# Chat Assistant Component - Usage Guide

## Overview
The ChatAssistant component is a minimalist, collapsible chat interface integrated into the Personal Ops Center. It provides users with AI-powered assistance for task management.

## Component Structure

```
ChatAssistant/
├── ChatAssistant.tsx      # Main component with state management
├── ChatMessage.tsx        # Individual message bubble component
├── ChatInput.tsx          # Input field and send button
├── ChatAssistant.css      # Minimalist styling
└── index.ts               # Export file
```

## Features

### 1. Collapsible Interface
- Floating action button in bottom-right corner
- Expands to show full chat window
- Minimizes back to button
- Smooth animations

### 2. Message Thread
- User messages (blue bubbles, right-aligned)
- Assistant messages (white bubbles, left-aligned)
- Timestamps on each message
- Auto-scroll to latest message
- Typing indicator animation

### 3. Input System
- Text input field with placeholder
- Send button (disabled when empty)
- Form submission on Enter key
- Auto-focus for better UX

### 4. Design Features
- Matches minimalist design system
- White backgrounds with thin borders
- Solid blue accent color
- Minimal shadows
- Professional avatar icon
- Responsive for mobile devices

## Usage

### Basic Integration (Already Done)
```tsx
import ChatAssistant from './components/ChatAssistant'

function Layout() {
  return (
    <div className="layout">
      {/* Other components */}
      <ChatAssistant />
    </div>
  )
}
```

### Message Structure
```typescript
interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
}
```

## API Integration

### Current Implementation
The component currently uses a mock response system. To integrate with a real backend:

1. **Update the API endpoint** in `/frontend/src/api/chat.ts`:
```typescript
const API_BASE_URL = 'http://localhost:8001'  // Your backend URL
```

2. **Replace mock response** in `ChatAssistant.tsx`:
```typescript
const handleSendMessage = async (content: string) => {
  const newMessage: Message = {
    id: Date.now().toString(),
    content,
    sender: 'user',
    timestamp: new Date()
  }

  setMessages(prev => [...prev, newMessage])
  setIsTyping(true)

  try {
    // Use the real API
    const response = await chatAPI.sendMessage({
      content,
      context: {
        currentView: window.location.pathname,
      }
    })

    const aiResponse: Message = {
      id: response.message.id,
      content: response.message.content,
      sender: 'assistant',
      timestamp: new Date(response.message.timestamp)
    }

    setMessages(prev => [...prev, aiResponse])
  } catch (error) {
    console.error('Error sending message:', error)
    // Handle error
  } finally {
    setIsTyping(false)
  }
}
```

## Backend Requirements

### Expected Endpoints

#### 1. Send Message
```
POST /api/chat/message
Content-Type: application/json

{
  "content": "User message here",
  "sessionId": "optional-session-id",
  "context": {
    "currentView": "/today",
    "selectedItems": []
  }
}

Response:
{
  "message": {
    "id": "msg-123",
    "content": "AI response here",
    "sender": "assistant",
    "timestamp": "2025-11-15T13:40:00Z"
  },
  "sessionId": "session-abc"
}
```

#### 2. Get History
```
GET /api/chat/history/{sessionId}

Response:
[
  {
    "id": "msg-1",
    "content": "Previous message",
    "sender": "user",
    "timestamp": "2025-11-15T13:30:00Z"
  },
  ...
]
```

## WebSocket Integration (Future)

For real-time responses, implement WebSocket support:

```typescript
// In ChatAssistant.tsx
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8001/ws/chat')

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data)
    setMessages(prev => [...prev, message])
    setIsTyping(false)
  }

  return () => ws.close()
}, [])
```

## Customization

### Styling
All styles are in `ChatAssistant.css`. Key CSS variables used:
- `--color-surface`: Background color
- `--color-accent-primary`: Primary blue color
- `--color-border-light`: Border color
- `--shadow-xl`: Shadow for floating elements

### Position
To change the position, update in `ChatAssistant.css`:
```css
.chat-assistant {
  position: fixed;
  bottom: 2rem;  /* Distance from bottom */
  right: 2rem;   /* Distance from right */
}
```

### Size
Adjust chat window dimensions:
```css
.chat-window {
  width: 380px;   /* Window width */
  height: 600px;  /* Window height */
}
```

## Responsive Behavior

### Desktop (> 768px)
- 380px wide window
- Bottom-right corner
- Rounded corners

### Mobile (≤ 768px)
- Smaller toggle button
- Constrained width
- Maintains rounded corners

### Small Mobile (≤ 480px)
- Full-screen chat window
- No rounded corners
- Covers entire viewport when open

## Accessibility

### Current Features
- ARIA labels on buttons
- Keyboard navigation support
- Auto-focus on input
- Clear visual states

### Future Improvements
- Screen reader announcements for new messages
- Keyboard shortcuts (Esc to close)
- Focus trap when open
- High contrast mode support

## Performance Considerations

1. **Message History**: Consider implementing pagination for long conversations
2. **Auto-scroll**: Uses `scrollIntoView` with smooth behavior
3. **Animations**: CSS animations for performance
4. **State Management**: React hooks for lightweight state

## Testing

### Manual Testing Checklist
- [ ] Toggle button opens/closes chat
- [ ] Messages appear in correct order
- [ ] Input clears after sending
- [ ] Typing indicator shows during response
- [ ] Auto-scroll to latest message
- [ ] Timestamps display correctly
- [ ] Responsive on mobile devices
- [ ] Close button works

### Unit Tests (To Add)
```typescript
describe('ChatAssistant', () => {
  test('renders toggle button when closed', () => {
    // Test implementation
  })

  test('sends message on form submit', () => {
    // Test implementation
  })

  test('displays typing indicator', () => {
    // Test implementation
  })
})
```

## Troubleshooting

### Chat won't open
- Check console for errors
- Verify ChatAssistant is imported in Layout
- Check z-index conflicts

### Messages not sending
- Verify API endpoint is correct
- Check network tab for failed requests
- Ensure backend is running

### Styling issues
- Check CSS variable definitions in index.css
- Verify ChatAssistant.css is imported
- Check for CSS conflicts

## Future Enhancements

1. **Rich Messages**: Support for markdown, links, buttons
2. **Voice Input**: Speech-to-text integration
3. **File Sharing**: Upload documents or images
4. **Message Actions**: Copy, edit, delete messages
5. **Conversations**: Multiple conversation threads
6. **Quick Replies**: Suggested response buttons
7. **Persistent Storage**: Save conversation history
8. **Notifications**: New message alerts when minimized

## Support

For issues or questions:
1. Check this guide first
2. Review the code comments
3. Check the build logs
4. Test in isolation (separate test page)

## Version History

### v1.0.0 (2025-11-15)
- Initial implementation
- Minimalist design
- Basic message threading
- Mock response system
- Responsive layout
- Integration with Layout component
