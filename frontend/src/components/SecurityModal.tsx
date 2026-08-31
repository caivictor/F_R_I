import React from "react";
import { ShieldCheck, X, RefreshCw, CheckCircle2, XCircle } from "lucide-react";
import type { SecurityAuditReport } from "../types";

interface SecurityModalProps {
  isOpen: boolean;
  auditReport: SecurityAuditReport | null;
  isLoading: boolean;
  onClose: () => void;
  onRefresh: () => void;
}

export const SecurityModal: React.FC<SecurityModalProps> = ({
  isOpen,
  auditReport,
  isLoading,
  onClose,
  onRefresh,
}) => {
    React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#0f172a] border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0c1222]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-950/80 border border-emerald-800/60 text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                Security Agent Posture Audit
              </h2>
              <p className="text-xs text-slate-400">
                System guardrails, sanitization controls, and transaction integrity checks
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Security Score Overview */}
        <div className="p-6 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-1">
              Overall System Security Status
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold font-mono text-emerald-400">
                {auditReport?.overall_status || "SECURE"}
              </span>
              <span className="px-2.5 py-0.5 text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800 rounded-md">
                Score: {auditReport?.security_score ?? 100}%
              </span>
            </div>
          </div>
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Re-Audit</span>
          </button>
        </div>

        {/* Audit controls list */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {isLoading && !auditReport ? (
            <div className="flex items-center justify-center py-12 text-slate-400 text-sm">
              <div className="w-5 h-5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mr-2" />
              Running security posture inspection...
            </div>
          ) : !auditReport?.audit_results || auditReport.audit_results.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-sm">
              No audit results available. Click Re-Audit to scan.
            </div>
          ) : (
            auditReport.audit_results.map((check, idx) => {
              const isPass = check.status === "PASS";
              return (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/60 flex items-start gap-3"
                >
                  <div className="mt-0.5">
                    {isPass ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-xs font-bold text-slate-200 font-mono">
                        {check.control}
                      </span>
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                          isPass
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            : "bg-rose-950 text-rose-300 border border-rose-800"
                        }`}
                      >
                        {check.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{check.details}</p>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
