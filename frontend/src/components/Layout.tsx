import { Link, Outlet, useLocation } from 'react-router-dom';
import { FileText, MessageSquare, LayoutDashboard, ScrollText } from 'lucide-react';
import { UserSwitcher } from './UserSwitcher';
import type { UserInfo } from '../types';
import { cn } from '../lib/utils';

interface Props {
  users: UserInfo[];
  currentUser: UserInfo;
  onSwitchUser: (userId: string) => void;
}

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/invoices', label: 'Invoices', icon: FileText },
  { path: '/feedback', label: 'Feedback', icon: MessageSquare },
  { path: '/prompts', label: 'Prompts', icon: ScrollText, adminOnly: true },
];

export function Layout({ users, currentUser, onSwitchUser }: Props) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-40 border-b border-gray-200 bg-white">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2">
              <FileText className="h-6 w-6 text-blue-600" />
              <span className="text-lg font-semibold text-gray-900">Invoice Agent</span>
            </Link>
            <nav className="hidden md:flex items-center gap-1">
              {navItems
                .filter((item) => !item.adminOnly || currentUser.role === 'admin')
                .map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      (item.path === '/' ? location.pathname === '/' : location.pathname.startsWith(item.path))
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                ))}
            </nav>
          </div>
          <UserSwitcher users={users} currentUser={currentUser} onSwitch={onSwitchUser} />
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}
