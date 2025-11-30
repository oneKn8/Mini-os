/**
 * ProgressTimeline - Multi-step progress visualization
 *
 * Shows progress for multi-tool agent queries
 */

interface ProgressStep {
  name: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  duration?: number;
}

interface ProgressTimelineProps {
  steps: ProgressStep[];
  currentAction?: string;
}

export function ProgressTimeline({ steps, currentAction }: ProgressTimelineProps) {
  if (steps.length === 0) {
    return null;
  }

  const completedCount = steps.filter((s) => s.status === 'completed').length;
  const progress = (completedCount / steps.length) * 100;

  return (
    <div
      style={{
        position: 'fixed',
        top: '80px',
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        borderRadius: '12px',
        padding: '16px 24px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
        zIndex: 9999,
        minWidth: '400px',
        maxWidth: '600px',
        animation: 'slideDown 0.3s ease-out',
      }}
    >
      <div style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#374151' }}>
            {currentAction || 'Processing...'}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            {completedCount}/{steps.length} complete
          </div>
        </div>

        <div
          style={{
            width: '100%',
            height: '4px',
            background: '#e5e7eb',
            borderRadius: '2px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${progress}%`,
              height: '100%',
              background: 'linear-gradient(90deg, rgb(59, 130, 246), rgb(147, 51, 234))',
              transition: 'width 0.3s ease-out',
            }}
          />
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {steps.map((step, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '12px',
              color: step.status === 'completed' ? '#6b7280' : '#374151',
            }}
          >
            <div
              style={{
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background:
                  step.status === 'completed'
                    ? 'rgb(16, 185, 129)'
                    : step.status === 'active'
                    ? 'rgb(59, 130, 246)'
                    : step.status === 'error'
                    ? 'rgb(239, 68, 68)'
                    : '#e5e7eb',
                color: 'white',
                flexShrink: 0,
                animation: step.status === 'active' ? 'spin 1s linear infinite' : 'none',
              }}
            >
              {step.status === 'completed' ? (
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path
                    d="M2 5L4 7L8 3"
                    stroke="white"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              ) : step.status === 'error' ? (
                <div style={{ fontSize: '10px', fontWeight: 'bold' }}>!</div>
              ) : step.status === 'active' ? (
                <div style={{ fontSize: '8px' }}>⟳</div>
              ) : null}
            </div>

            <div style={{ flex: 1 }}>{step.name}</div>

            {step.duration && (
              <div style={{ fontSize: '11px', color: '#9ca3af' }}>{step.duration}ms</div>
            )}
          </div>
        ))}
      </div>

      <style>
        {`
          @keyframes slideDown {
            from {
              opacity: 0;
              transform: translateX(-50%) translateY(-10px);
            }
            to {
              opacity: 1;
              transform: translateX(-50%) translateY(0);
            }
          }

          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
}
