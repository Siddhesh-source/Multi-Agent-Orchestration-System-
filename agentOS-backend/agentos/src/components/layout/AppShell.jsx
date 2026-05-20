import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { LayoutDashboard, ListTodo, Database, Settings } from 'lucide-react'
import TopBar from './TopBar'

// ─── Mobile detection ─────────────────────────────────────────────────
function useIsMobile() {
    const [mobile, setMobile] = useState(
        () => typeof window !== 'undefined' && window.innerWidth < 768
    )
    useEffect(() => {
        const mq = window.matchMedia('(max-width: 767px)')
        const handler = (e) => setMobile(e.matches)
        mq.addEventListener('change', handler)
        return () => mq.removeEventListener('change', handler)
    }, [])
    return mobile
}

// ─── Nav items ───────────────────────────────────────────────────────
const NAV = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
    { to: '/task', icon: ListTodo, label: 'Tasks' },
    { to: '/memory', icon: Database, label: 'Memory' },
]

// ─── Desktop nav icon ─────────────────────────────────────────────────
function SideNavIcon({ to, icon: Icon, label, end }) {
    return (
        <NavLink
            to={to}
            end={end}
            aria-label={label}
            style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '36px',
                height: '36px',
                borderRadius: '6px',
                color: isActive ? '#00D9FF' : '#3A3A4A',
                textDecoration: 'none',
                flexShrink: 0,
                transition: 'color 150ms ease',
            })}
            onMouseEnter={(e) => {
                const link = e.currentTarget
                if (link.style.color !== 'rgb(0, 217, 255)')
                    link.style.color = '#6B7280'
            }}
            onMouseLeave={(e) => {
                const link = e.currentTarget
                if (link.style.color !== 'rgb(0, 217, 255)')
                    link.style.color = '#3A3A4A'
            }}
        >
            {({ isActive }) => (
                <Icon size={18} strokeWidth={isActive ? 2 : 1.5} />
            )}
        </NavLink>
    )
}

// ─── Mobile bottom nav icon ───────────────────────────────────────────
function BottomNavIcon({ to, icon: Icon, label, end }) {
    return (
        <NavLink
            to={to}
            end={end}
            aria-label={label}
            style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flex: 1,
                height: '100%',
                color: isActive ? '#00D9FF' : '#3A3A4A',
                textDecoration: 'none',
                transition: 'color 150ms ease',
            })}
        >
            {({ isActive }) => (
                <Icon size={20} strokeWidth={isActive ? 2 : 1.5} />
            )}
        </NavLink>
    )
}

// ─── AppShell ─────────────────────────────────────────────────────────
export default function AppShell() {
    const location = useLocation()
    const isMobile = useIsMobile()

    return (
        <div
            style={{
                display: 'flex',
                flexDirection: isMobile ? 'column' : 'row',
                height: '100vh',
                width: '100vw',
                overflow: 'hidden',
                backgroundColor: '#0A0A0F',
            }}
        >
            {/* ── Desktop sidebar ───────────────────────────────────────── */}
            {!isMobile && (
                <aside
                    style={{
                        width: '52px',
                        flexShrink: 0,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        borderRight: '1px solid #1E1E2E',
                        backgroundColor: '#0A0A0F',
                        paddingTop: '16px',
                        paddingBottom: '16px',
                    }}
                >
                    {/* Logo */}
                    <div
                        style={{
                            fontFamily: "'DM Mono', monospace",
                            fontSize: '13px',
                            color: '#00D9FF',
                            letterSpacing: '0.15em',
                            fontWeight: 500,
                            marginBottom: '28px',
                            userSelect: 'none',
                        }}
                    >
                        AOS
                    </div>

                    {/* Primary nav */}
                    <nav style={{ display: 'flex', flexDirection: 'column', gap: '32px', flex: 1 }}>
                        {NAV.map(({ to, icon, label, end }) => (
                            <SideNavIcon key={to} to={to} icon={icon} label={label} end={end} />
                        ))}
                    </nav>

                    <SideNavIcon to="/settings" icon={Settings} label="Settings" />
                </aside>
            )}

            {/* ── Main column ───────────────────────────────────────────── */}
            <div
                style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                    minWidth: 0,
                    minHeight: 0,
                }}
            >
                <TopBar />

                {/* Animated page content */}
                <AnimatePresence mode="wait">
                    <motion.main
                        key={location.pathname}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        transition={{ duration: 0.18, ease: 'easeOut' }}
                        style={{
                            flex: 1,
                            overflowY: 'auto',
                            padding: '24px',
                            minHeight: 0,
                        }}
                    >
                        <Outlet />
                    </motion.main>
                </AnimatePresence>
            </div>

            {/* ── Mobile bottom nav ─────────────────────────────────────── */}
            {isMobile && (
                <nav
                    style={{
                        height: '52px',
                        flexShrink: 0,
                        display: 'flex',
                        alignItems: 'center',
                        borderTop: '1px solid #1E1E2E',
                        backgroundColor: '#0A0A0F',
                    }}
                >
                    {NAV.map(({ to, icon, label, end }) => (
                        <BottomNavIcon key={to} to={to} icon={icon} label={label} end={end} />
                    ))}
                    <BottomNavIcon to="/settings" icon={Settings} label="Settings" />
                </nav>
            )}
        </div>
    )
}
