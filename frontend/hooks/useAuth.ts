/**
 * LK Clinic Tools - Auth Hook
 * Manages authentication state and user context.
 */

"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";

export interface User {
  auth_user_id: string;
  user_id: string;
  clinic_id: string | null;
  email: string;
  name: string;
  role: "agency_admin" | "agency_operator" | "clinic_admin" | "clinic_staff";
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        fetchUser();
      } else {
        setLoading(false);
      }
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        fetchUser();
      } else {
        setUser(null);
        setLoading(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  async function fetchUser() {
    try {
      const userData = await api.get<User>("/auth/me");
      setUser(userData);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function signIn(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
    // Fetch user profile using the token from the sign-in response directly
    if (data.session?.access_token) {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${API_URL}/api/auth/me`, {
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${data.session.access_token}`,
          },
        });
        if (res.ok) {
          const userData = await res.json();
          setUser(userData);
        }
      } catch {
        // Will be retried by onAuthStateChange
      }
    }
  }

  async function signOut() {
    await supabase.auth.signOut();
    setUser(null);
  }

  const isAgency =
    user?.role === "agency_admin" || user?.role === "agency_operator";
  const isClinicAdmin = user?.role === "clinic_admin";
  const isStaff = user?.role === "clinic_staff";

  return {
    user,
    loading,
    signIn,
    signOut,
    isAgency,
    isClinicAdmin,
    isStaff,
    isAuthenticated: !!user,
  };
}
