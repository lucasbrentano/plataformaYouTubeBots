import { useState } from "react";
import { useAuthContext } from "../../contexts/AuthContext";
import { useAuth } from "../Auth/useAuth";
import { CreateUserModal } from "./CreateUserModal";
import { useUsers } from "./useUsers";
import styles from "./UsersPage.module.css";

export function UsersPage() {
  const { user } = useAuthContext();
  const { logout } = useAuth();
  const { users, loading, error, createUser, deleteUser } = useUsers();
  const [showModal, setShowModal] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await deleteUser(id);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className={styles.layout}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.brand}>
          <div className={styles.brandIcon} aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 40 40" fill="none">
              <rect width="40" height="40" rx="10" fill="#6c5fc7" />
              <path d="M10 28L20 12L30 28" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M14 22H26" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
            </svg>
          </div>
          <span className={styles.brandName}>Plataforma YouTube Bots</span>
        </div>
        <div className={styles.headerActions}>
          <span className={styles.userInfo}>
            <span className="badge badge-admin">{user?.role}</span>
            {user?.username}
          </span>
          <button className="btn btn-ghost" onClick={() => void logout()}>
            Sair
          </button>
        </div>
      </header>

      {/* Conteúdo */}
      <main className={styles.main}>
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <h1 className={styles.pageTitle}>Usuários</h1>
              <p className={styles.pageDesc}>Gerencie as contas de acesso à plataforma.</p>
            </div>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              + Criar Pesquisador
            </button>
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          {loading ? (
            <div className={styles.emptyState}>Carregando usuários…</div>
          ) : users.length === 0 ? (
            <div className={styles.emptyState}>Nenhum usuário encontrado.</div>
          ) : (
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Usuário</th>
                    <th>Papel</th>
                    <th>Criado em</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td className={styles.colUsername}>
                        <span className={styles.avatar}>{u.username[0].toUpperCase()}</span>
                        {u.username}
                      </td>
                      <td>
                        <span className={`badge ${u.role === "admin" ? "badge-admin" : "badge-user"}`}>
                          {u.role}
                        </span>
                      </td>
                      <td className={styles.colDate}>
                        {new Date(u.created_at).toLocaleDateString("pt-BR", {
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                        })}
                      </td>
                      <td className={styles.colAction}>
                        {u.username !== user?.username && (
                          <button
                            className="btn btn-danger"
                            disabled={deletingId === u.id}
                            onClick={() => void handleDelete(u.id)}
                          >
                            {deletingId === u.id ? "Removendo…" : "Remover"}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {showModal && (
        <CreateUserModal onClose={() => setShowModal(false)} onCreate={createUser} />
      )}
    </div>
  );
}
