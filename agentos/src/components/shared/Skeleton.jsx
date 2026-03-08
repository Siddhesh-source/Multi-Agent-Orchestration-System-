/**
 * Skeleton — animated shimmer placeholder block.
 * Uses aos-shimmer keyframe defined in index.css.
 */
export default function Skeleton({ width = '100%', height = '10px', style = {} }) {
    return (
        <div
            style={{
                width,
                height,
                borderRadius: '2px',
                background: 'linear-gradient(90deg, #111118 0%, #1E1E2E 50%, #111118 100%)',
                backgroundSize: '600px 100%',
                animation: 'aos-shimmer 1.6s infinite linear',
                flexShrink: 0,
                ...style,
            }}
        />
    )
}

/** Pre-composed row of skeletons for a task/memory list item. */
export function SkeletonRow() {
    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                padding: '10px 0',
                borderBottom: '1px solid #1E1E2E',
            }}
        >
            <Skeleton width="60%" />
            <Skeleton width="14%" />
            <Skeleton width="8%" />
        </div>
    )
}
