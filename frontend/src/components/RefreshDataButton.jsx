import { useState } from "react";
import { clearDataCache } from "@/lib/dataCacheApi";

const OUTLINE_BUTTON =
  "rounded-md border border-gold px-3 py-1.5 text-xs font-medium text-gold transition-colors hover:bg-gold hover:text-background disabled:opacity-60";

// Estados: idle -> confirming -> working -> (recarga de la pagina) | error.
// Tras borrar se recarga la pagina entera: asi todas las pantallas vuelven a
// pedir sus datos y el backend los descarga de Yahoo Finance bajo demanda.
function RefreshDataButton() {
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");

  async function handleConfirm() {
    setStatus("working");
    try {
      const result = await clearDataCache();
      if (result.failed.length > 0) {
        const names = result.failed.map((f) => f.file).join(", ");
        setMessage(`Could not delete ${result.failed.length} file(s): ${names}. Close whatever is using them and try again.`);
        setStatus("error");
        return;
      }
      window.location.reload();
    } catch (err) {
      setMessage(err.message);
      setStatus("error");
    }
  }

  const panelOpen = status === "confirming" || status === "error";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setStatus(panelOpen ? "idle" : "confirming")}
        disabled={status === "working"}
        aria-expanded={panelOpen}
        className={OUTLINE_BUTTON}
      >
        {status === "working" ? "Clearing…" : "Refresh data"}
      </button>

      {panelOpen && (
        <div className="absolute right-0 top-full z-50 mt-2 w-72 rounded-md border border-border bg-card p-3 text-xs shadow-lg">
          {status === "confirming" ? (
            <>
              <p className="text-foreground">
                Delete all downloaded data (raw and processed) and clear the cache?
              </p>
              <p className="mt-1 text-muted-foreground">
                Each ticker is downloaded again from Yahoo Finance the next time a screen needs it.
                Hourly history is limited to roughly the last 2 years.
              </p>
              <div className="mt-3 flex justify-end gap-2">
                <button type="button" onClick={() => setStatus("idle")} className={OUTLINE_BUTTON}>
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirm}
                  className="rounded-md bg-gold px-3 py-1.5 text-xs font-medium text-background transition-opacity hover:opacity-90"
                >
                  Delete and refresh
                </button>
              </div>
            </>
          ) : (
            <>
              <p className="text-destructive">{message}</p>
              <div className="mt-3 flex justify-end">
                <button type="button" onClick={() => setStatus("idle")} className={OUTLINE_BUTTON}>
                  Close
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default RefreshDataButton;
