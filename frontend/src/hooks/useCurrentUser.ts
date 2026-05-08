import { useState, useEffect, useCallback } from 'react';
import type { UserInfo } from '../types';
import { api } from '../services/api';

// Mirrors the hardcoded users in backend/config.py — used for instant
// initialisation from localStorage without waiting for the API call.
const KNOWN_USERS: UserInfo[] = [
  { id: 'admin-jane', name: 'Jane (Admin)', role: 'admin' },
  { id: 'admin-bob',  name: 'Bob (Admin)',  role: 'admin' },
  { id: 'user-john',  name: 'John',         role: 'user'  },
  { id: 'user-sarah', name: 'Sarah',        role: 'user'  },
];

function resolveUser(id: string | null): UserInfo {
  return KNOWN_USERS.find((u) => u.id === id) ?? KNOWN_USERS[2]; // default: John
}

export function useCurrentUser() {
  const [users, setUsers] = useState<UserInfo[]>(KNOWN_USERS);
  const [currentUser, setCurrentUser] = useState<UserInfo>(
    // Resolve immediately from localStorage — no API wait
    () => resolveUser(localStorage.getItem('currentUserId'))
  );

  useEffect(() => {
    // Sync with backend in case users change, but we already have a value
    api.getUsers()
      .then((userList) => {
        setUsers(userList);
        const storedId = localStorage.getItem('currentUserId');
        const match = userList.find((u) => u.id === storedId) ?? userList[0];
        if (match) {
          setCurrentUser(match);
          localStorage.setItem('currentUserId', match.id);
        }
      })
      .catch(console.error);
  }, []);

  const switchUser = useCallback((userId: string) => {
    const user = users.find((u) => u.id === userId);
    if (user) {
      setCurrentUser(user);
      localStorage.setItem('currentUserId', user.id);
    }
  }, [users]);

  return { users, currentUser, switchUser };
}
