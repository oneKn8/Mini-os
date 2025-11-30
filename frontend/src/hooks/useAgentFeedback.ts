/**
 * useAgentFeedback - Hook for consuming visual feedback events from agent
 *
 * Listens to WebSocket events and provides:
 * - Element highlights (thinking, working, done, error states)
 * - Ghost previews for upcoming changes
 * - Progress animations
 */

import { useEffect, useState, useCallback } from 'react';
import { useAgentWebSocket } from './useAgentWebSocket';

export interface HighlightEvent {
  type: 'highlight';
  selector: string;
  state: 'thinking' | 'working' | 'done' | 'error';
  message: string;
  duration_ms: number;
  color?: string;
  timestamp: string;
}

export interface GhostPreviewEvent {
  type: 'ghost_preview';
  component_type: string;
  data: Record<string, any>;
  action: 'create' | 'update' | 'delete';
  preview_id: string;
  requires_confirmation: boolean;
  timestamp: string;
}

export interface AnimationEvent {
  type: 'animation';
  animation_type: string;
  target_selector: string;
  duration_ms: number;
  timestamp: string;
}

export interface ActiveHighlight {
  selector: string;
  state: 'thinking' | 'working' | 'done' | 'error';
  message: string;
  color?: string;
  expiresAt: number;
}

export interface ActivePreview {
  id: string;
  componentType: string;
  data: Record<string, any>;
  action: 'create' | 'update' | 'delete';
  requiresConfirmation: boolean;
}

export interface UseAgentFeedbackReturn {
  highlights: Map<string, ActiveHighlight>;
  previews: Map<string, ActivePreview>;
  animations: AnimationEvent[];
  confirmPreview: (previewId: string) => void;
  dismissPreview: (previewId: string) => void;
}

export function useAgentFeedback(): UseAgentFeedbackReturn {
  const { lastEvent } = useAgentWebSocket({ sessionId: null, enabled: true });

  const [highlights, setHighlights] = useState<Map<string, ActiveHighlight>>(new Map());
  const [previews, setPreviews] = useState<Map<string, ActivePreview>>(new Map());
  const [animations, setAnimations] = useState<AnimationEvent[]>([]);

  // Handle highlight events
  useEffect(() => {
    if (!lastEvent || lastEvent.type !== 'highlight') return;

    const event = lastEvent as HighlightEvent;
    const expiresAt = Date.now() + event.duration_ms;

    setHighlights((prev) => {
      const next = new Map(prev);
      next.set(event.selector, {
        selector: event.selector,
        state: event.state,
        message: event.message,
        color: event.color,
        expiresAt,
      });
      return next;
    });

    // Auto-remove after duration
    const timeout = setTimeout(() => {
      setHighlights((prev) => {
        const next = new Map(prev);
        next.delete(event.selector);
        return next;
      });
    }, event.duration_ms);

    return () => clearTimeout(timeout);
  }, [lastEvent]);

  // Handle ghost preview events
  useEffect(() => {
    if (!lastEvent || lastEvent.type !== 'ghost_preview') return;

    const event = lastEvent as GhostPreviewEvent;

    setPreviews((prev) => {
      const next = new Map(prev);
      next.set(event.preview_id, {
        id: event.preview_id,
        componentType: event.component_type,
        data: event.data,
        action: event.action,
        requiresConfirmation: event.requires_confirmation,
      });
      return next;
    });
  }, [lastEvent]);

  // Handle animation events
  useEffect(() => {
    if (!lastEvent || lastEvent.type !== 'animation') return;

    const event = lastEvent as AnimationEvent;

    setAnimations((prev) => [...prev, event]);

    // Remove after duration
    setTimeout(() => {
      setAnimations((prev) => prev.filter((a) => a !== event));
    }, event.duration_ms + 100);
  }, [lastEvent]);

  const confirmPreview = useCallback((previewId: string) => {
    // TODO: Send confirmation to backend
    console.log('Confirming preview:', previewId);

    setPreviews((prev) => {
      const next = new Map(prev);
      next.delete(previewId);
      return next;
    });
  }, []);

  const dismissPreview = useCallback((previewId: string) => {
    setPreviews((prev) => {
      const next = new Map(prev);
      next.delete(previewId);
      return next;
    });
  }, []);

  return {
    highlights,
    previews,
    animations,
    confirmPreview,
    dismissPreview,
  };
}
