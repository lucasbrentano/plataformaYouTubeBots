import { FormEvent, useState } from "react";
import { UserCreate } from "../../api/auth";
import styles from "./CreateUserModal.module.css";

interface Props {
  onClose: () => void;
  onCreate: (data: UserCreate) => Promise<void>;
}

export function CreateUserModal({ onClose, onCreate }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"admin" | "user">("user");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await onCreate({ username, password, role });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar usuário");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>Criar Usuário</h2>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Fechar">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className={styles.body}>
            <div className="form-group">
              <label className="form-label" htmlFor="new-username">
                Usuário
              </label>
              <input
                id="new-username"
                className="form-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                minLength={3}
                maxLength={64}
                autoFocus
                placeholder="mínimo 3 caracteres"
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="new-password">
                Senha
              </label>
              <input
                id="new-password"
                className="form-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                placeholder="mínimo 8 caracteres"
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="new-role">
                Papel
              </label>
              <select
                id="new-role"
                className="form-select"
                value={role}
                onChange={(e) => setRole(e.target.value as "admin" | "user")}
              >
                <option value="user">user — coleta, limpeza, anotação</option>
                <option value="admin">admin — acesso total</option>
              </select>
            </div>

            {error && <div className="alert alert-error" style={{ marginTop: 16 }}>{error}</div>}
          </div>

          <div className={styles.footer}>
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Criando…" : "Criar Usuário"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
