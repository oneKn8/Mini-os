/**
 * ElementHighlight - Cursor-style element highlighting
 *
 * Highlights UI elements based on agent actions:
 * - thinking: Blue pulse
 * - working: Yellow shine
 * - done: Green checkmark
 * - error: Red shake
 */

import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useAgentFeedback } from '../../hooks/useAgentFeedback';

const STATE_COLORS = {
  thinking: {
    border: 'rgb(59, 130, 246)',
    bg: 'rgba(59, 130, 246, 0.1)',
    shadow: '0 0 20px rgba(59, 130, 246, 0.5)',
  },
  working: {
    border: 'rgb(251, 191, 36)',
    bg: 'rgba(251, 191, 36, 0.1)',
    shadow: '0 0 20px rgba(251, 191, 36, 0.5)',
  },
  done: {
    border: 'rgb(16, 185, 129)',
    bg: 'rgba(16, 185, 129, 0.1)',
    shadow: '0 0 20px rgba(16, 185, 129, 0.5)',
  },
  error: {
    border: 'rgb(239, 68, 68)',
    bg: 'rgba(239, 68, 68, 0.1)',
    shadow: '0 0 20px rgba(239, 68, 68, 0.5)',
  },
};

interface HighlightOverlayProps {
  selector: string;
  state: 'thinking' | 'working' | 'done' | 'error';
  message: string;
  color?: string;
}

function HighlightOverlay({ selector, state, message, color }: HighlightOverlayProps) {
  const [element, setElement] = useState<Element | null>(null);
  const [bounds, setBounds] = useState<DOMRect | null>(null);

  useEffect(() => {
    const targetElement = document.querySelector(selector);
    setElement(targetElement);

    if (targetElement) {
      const updateBounds = () => {
        setBounds(targetElement.getBoundingClientRect());
      };

      updateBounds();

      // Update on scroll/resize
      window.addEventListener('scroll', updateBounds, true);
      window.addEventListener('resize', updateBounds);

      return () => {
        window.removeEventListener('scroll', updateBounds, true);
        window.removeEventListener('resize', updateBounds);
      };
    }
  }, [selector]);

  if (!element || !bounds) {
    return null;
  }

  const stateStyle = STATE_COLORS[state];
  const borderColor = color || stateStyle.border;

  return createPortal(
    <div
      style={{
        position: 'fixed',
        top: bounds.top - 4,
        left: bounds.left - 4,
        width: bounds.width + 8,
        height: bounds.height + 8,
        border: `2px solid ${borderColor}`,
        borderRadius: '8px',
        background: stateStyle.bg,
        boxShadow: stateStyle.shadow,
        pointerEvents: 'none',
        zIndex: 9998,
        transition: 'all 0.3s ease',
        animation:
          state === 'thinking'
            ? 'pulse 2s ease-in-out infinite'
            : state === 'working'
            ? 'shine 1s ease-in-out infinite'
            : state === 'error'
            ? 'shake 0.5s ease-in-out'
            : state === 'done'
            ? 'fadeOut 2s ease-out forwards'
            : 'none',
      }}
    >
      {message && (
        <div
          style={{
            position: 'absolute',
            top: '-32px',
            left: '0',
            background: borderColor,
            color: 'white',
            padding: '4px 12px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 500,
            whiteSpace: 'nowrap',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
          }}
        >
          {message}
        </div>
      )}

      {state === 'done' && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: 'rgb(16, 185, 129)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            animation: 'checkmark 0.5s ease-out',
          }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M4 10L8 14L16 6"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      )}

      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.02); }
          }

          @keyframes shine {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
          }

          @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-4px); }
            75% { transform: translateX(4px); }
          }

          @keyframes fadeOut {
            0% { opacity: 1; }
            70% { opacity: 1; }
            100% { opacity: 0; }
          }

          @keyframes checkmark {
            0% { transform: translate(-50%, -50%) scale(0); opacity: 0; }
            50% { transform: translate(-50%, -50%) scale(1.2); }
            100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
          }
        `}
      </style>
    </div>,
    document.body
  );
}

export function ElementHighlight() {
  const { highlights } = useAgentFeedback();

  return (
    <>
      {Array.from(highlights.values()).map((highlight) => (
        <HighlightOverlay
          key={highlight.selector}
          selector={highlight.selector}
          state={highlight.state}
          message={highlight.message}
          color={highlight.color}
        />
      ))}
    </>
  );
}
