import { ChevronDown, Shield, User } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import type { UserInfo } from '../types';

interface Props {
  users: UserInfo[];
  currentUser: UserInfo;
  onSwitch: (userId: string) => void;
}

export function UserSwitcher({ users, currentUser, onSwitch }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium shadow-sm hover:bg-gray-50 transition-colors"
      >
        {currentUser.role === 'admin' ? (
          <Shield className="h-4 w-4 text-blue-600" />
        ) : (
          <User className="h-4 w-4 text-gray-500" />
        )}
        <span>{currentUser.name}</span>
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
          {currentUser.role}
        </span>
        <ChevronDown className="h-3 w-3 text-gray-400" />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-1 w-56 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
          <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase">
            Switch User
          </div>
          {users.map((u) => (
            <button
              key={u.id}
              onClick={() => { onSwitch(u.id); setOpen(false); }}
              className={`flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 ${
                u.id === currentUser.id ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
              }`}
            >
              {u.role === 'admin' ? (
                <Shield className="h-4 w-4 text-blue-600" />
              ) : (
                <User className="h-4 w-4 text-gray-400" />
              )}
              <span>{u.name}</span>
              <span className="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-xs">
                {u.role}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
