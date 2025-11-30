/**
 * GhostPreview - Preview upcoming changes before they happen
 *
 * Shows semi-transparent "ghost" components for:
 * - Email drafts
 * - Calendar events
 * - Tasks
 * - Other creations
 */

import { useAgentFeedback } from '../../hooks/useAgentFeedback';

interface GhostEmailProps {
  data: Record<string, any>;
  onConfirm: () => void;
  onDismiss: () => void;
}

function GhostEmail({ data, onConfirm, onDismiss }: GhostEmailProps) {
  return (
    <div
      style={{
        background: 'rgba(255, 255, 255, 0.5)',
        backdropFilter: 'blur(8px)',
        border: '2px dashed rgb(59, 130, 246)',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '12px',
        position: 'relative',
        animation: 'fadeInGhost 0.3s ease-out',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: '#374151' }}>
            {data.subject || 'Draft Email'}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
            To: {data.to || 'recipient'}
          </div>
          <div style={{ fontSize: '12px', color: '#9ca3af' }}>
            {data.body ? data.body.substring(0, 100) + '...' : 'Email body preview'}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', marginLeft: '16px' }}>
          <button
            onClick={onConfirm}
            style={{
              padding: '6px 12px',
              background: 'rgb(16, 185, 129)',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            Create
          </button>
          <button
            onClick={onDismiss}
            style={{
              padding: '6px 12px',
              background: 'rgb(229, 231, 235)',
              color: '#374151',
              border: 'none',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          top: '-10px',
          left: '12px',
          background: 'rgb(59, 130, 246)',
          color: 'white',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '10px',
          fontWeight: 600,
          textTransform: 'uppercase',
        }}
      >
        Preview
      </div>
    </div>
  );
}

interface GhostEventProps {
  data: Record<string, any>;
  onConfirm: () => void;
  onDismiss: () => void;
}

function GhostEvent({ data, onConfirm, onDismiss }: GhostEventProps) {
  return (
    <div
      style={{
        background: 'rgba(255, 255, 255, 0.5)',
        backdropFilter: 'blur(8px)',
        border: '2px dashed rgb(147, 51, 234)',
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '8px',
        position: 'relative',
        animation: 'fadeInGhost 0.3s ease-out',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#374151' }}>
            {data.title || 'New Event'}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
            {data.start_time || 'Time TBD'}
            {data.duration && ` • ${data.duration}`}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={onConfirm}
            style={{
              padding: '4px 10px',
              background: 'rgb(147, 51, 234)',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            Add
          </button>
          <button
            onClick={onDismiss}
            style={{
              padding: '4px 10px',
              background: 'rgb(229, 231, 235)',
              color: '#374151',
              border: 'none',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            No
          </button>
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          top: '-8px',
          left: '10px',
          background: 'rgb(147, 51, 234)',
          color: 'white',
          padding: '2px 6px',
          borderRadius: '3px',
          fontSize: '9px',
          fontWeight: 600,
          textTransform: 'uppercase',
        }}
      >
        Preview
      </div>
    </div>
  );
}

function GhostPreviewComponent({ preview, onConfirm, onDismiss }: any) {
  if (preview.componentType === 'email') {
    return <GhostEmail data={preview.data} onConfirm={onConfirm} onDismiss={onDismiss} />;
  }

  if (preview.componentType === 'event') {
    return <GhostEvent data={preview.data} onConfirm={onConfirm} onDismiss={onDismiss} />;
  }

  // Generic fallback
  return (
    <div
      style={{
        background: 'rgba(255, 255, 255, 0.5)',
        backdropFilter: 'blur(8px)',
        border: '2px dashed rgb(107, 114, 128)',
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '8px',
        animation: 'fadeInGhost 0.3s ease-out',
      }}
      data-preview-id={preview.id}
    >
      <div style={{ fontSize: '12px', color: '#6b7280' }}>
        Preview: {preview.componentType} ({preview.action})
      </div>
      <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
        <button onClick={onConfirm} style={{ padding: '4px 8px', fontSize: '11px' }}>
          Confirm
        </button>
        <button onClick={onDismiss} style={{ padding: '4px 8px', fontSize: '11px' }}>
          Cancel
        </button>
      </div>
    </div>
  );
}

export function GhostPreview() {
  const { previews, confirmPreview, dismissPreview } = useAgentFeedback();

  if (previews.size === 0) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        maxWidth: '400px',
      }}
    >
      <style>
        {`
          @keyframes fadeInGhost {
            from {
              opacity: 0;
              transform: translateY(10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}
      </style>

      {Array.from(previews.values()).map((preview) => (
        <GhostPreviewComponent
          key={preview.id}
          preview={preview}
          onConfirm={() => confirmPreview(preview.id)}
          onDismiss={() => dismissPreview(preview.id)}
        />
      ))}
    </div>
  );
}
