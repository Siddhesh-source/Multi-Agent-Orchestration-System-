/**
 * ErrorRow — inline error state with retry trigger.
 */
export default function ErrorRow({ onRetry, message = 'Failed to load.' }) {
    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '12px 0',
            }}
        >
            <span
                style={{
                    fontFamily: "'DM Mono', monospace",
                    fontSize: '10px',
                    color: '#EF4444',
                    letterSpacing: '0.03em',
                }}
            >
                {message}
            </span>
            <button
                onClick={onRetry}
                style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontFamily: "'DM Mono', monospace",
                    fontSize: '10px',
                    color: '#EF4444',
                    textDecoration: 'underline',
                    padding: 0,
                    letterSpacing: '0.03em',
                    transition: 'opacity 150ms ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.7')}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
            >
                Retry
            </button>
        </div>
    )
}
