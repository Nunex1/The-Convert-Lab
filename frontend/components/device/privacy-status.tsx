import { LockKeyhole } from "lucide-react";
export function PrivacyStatus() {
  return (
    <p className="privacy-status">
      <LockKeyhole size={12} />
      <span>Arquivos temporários excluídos após a conversão.</span>
    </p>
  );
}
