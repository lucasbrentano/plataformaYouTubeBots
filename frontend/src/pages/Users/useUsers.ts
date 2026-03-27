import { useCallback, useEffect, useState } from "react";
import { UserCreate, UserOut, authApi } from "../../api/auth";
import { useAuthContext } from "../../contexts/AuthContext";

export function useUsers() {
  const { token } = useAuthContext();
  const [users, setUsers] = useState<UserOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      setUsers(await authApi.listUsers(token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar usuários");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void fetchUsers();
  }, [fetchUsers]);

  const createUser = useCallback(
    async (data: UserCreate) => {
      if (!token) return;
      await authApi.createUser(data, token);
      await fetchUsers();
    },
    [token, fetchUsers],
  );

  const deleteUser = useCallback(
    async (userId: string) => {
      if (!token) return;
      await authApi.deleteUser(userId, token);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    },
    [token],
  );

  return { users, loading, error, createUser, deleteUser, refetch: fetchUsers };
}
