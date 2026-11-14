'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase, isSupabaseConfigured } from '@/lib/supabase/client';

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'finance_manager' | 'staff';
  department: string;
}

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  isSupabaseConnected: boolean;
  login: (email: string, password?: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  switchRole: (role: 'admin' | 'finance_manager' | 'staff') => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  isSupabaseConnected: false,
  login: async () => ({ success: false }),
  logout: async () => {},
  switchRole: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Supabase가 연결되어 있는 경우 세션 리스너 등록
    if (isSupabaseConfigured && supabase) {
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (session?.user) {
          setUser({
            id: session.user.id,
            email: session.user.email || 'user@hospital.com',
            name: session.user.user_metadata?.full_name || '정산 담당자',
            role: session.user.user_metadata?.role || 'finance_manager',
            department: session.user.user_metadata?.department || '병원사업본부',
          });
        }
        setLoading(false);
      });

      const { data: authListener } = supabase.auth.onAuthStateChange(
        (_event, session) => {
          if (session?.user) {
            setUser({
              id: session.user.id,
              email: session.user.email || 'user@hospital.com',
              name: session.user.user_metadata?.full_name || '정산 담당자',
              role: session.user.user_metadata?.role || 'finance_manager',
              department: session.user.user_metadata?.department || '병원사업본부',
            });
          } else {
            setUser(null);
          }
        }
      );

      return () => {
        authListener.subscription.unsubscribe();
      };
    } else {
      // 2. Mock/Demo 모드: localStorage에서 이전 로그인 상태 복구
      const savedUser = typeof window !== 'undefined' ? localStorage.getItem('clp_demo_user') : null;
      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser));
        } catch {
          setUser(null);
        }
      }
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password = ''): Promise<{ success: boolean; error?: string }> => {
    setLoading(true);
    if (isSupabaseConfigured && supabase) {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) {
        setLoading(false);
        return { success: false, error: error.message };
      }
      if (data.user) {
        setUser({
          id: data.user.id,
          email: data.user.email || email,
          name: data.user.user_metadata?.full_name || '정산 담당자',
          role: data.user.user_metadata?.role || 'finance_manager',
          department: data.user.user_metadata?.department || '병원사업본부',
        });
      }
      setLoading(false);
      return { success: true };
    } else {
      // Mock / Demo 계정 로그인
      let role: 'admin' | 'finance_manager' | 'staff' = 'finance_manager';
      let name = '이창환';
      let department = '병원사업부 / 정산총괄';

      if (email.includes('admin')) {
        role = 'admin';
        name = '시스템 관리자';
        department = 'IT 인프라팀';
      } else if (email.includes('staff')) {
        role = 'staff';
        name = '김정산 주임';
        department = '재무관리팀';
      }

      const mockUser: UserProfile = {
        id: 'usr-' + Math.random().toString(36).substring(2, 9),
        email,
        name,
        role,
        department,
      };

      setUser(mockUser);
      if (typeof window !== 'undefined') {
        localStorage.setItem('clp_demo_user', JSON.stringify(mockUser));
      }
      setLoading(false);
      return { success: true };
    }
  };

  const logout = async () => {
    if (isSupabaseConfigured && supabase) {
      await supabase.auth.signOut();
    }
    if (typeof window !== 'undefined') {
      localStorage.removeItem('clp_demo_user');
    }
    setUser(null);
  };

  const switchRole = (newRole: 'admin' | 'finance_manager' | 'staff') => {
    if (!user) return;
    const updated = { ...user, role: newRole };
    setUser(updated);
    if (typeof window !== 'undefined') {
      localStorage.setItem('clp_demo_user', JSON.stringify(updated));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isSupabaseConnected: isSupabaseConfigured,
        login,
        logout,
        switchRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
