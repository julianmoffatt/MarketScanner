import { useEffect, useState } from "react";
import { useTicker } from "../../analytics/hooks/useTicker";
import { getMLTraining } from "../api/mlApi";
import ScreenHeader from "../../analytics/components/ScreenHeader";
import ModelMetricsCard from "../components/ModelMetricsCard";

function MLTraining() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    setData(null);
    getMLTraining(ticker, { signal: controller.signal })
      .then((result) => {
        setData(result);
      })
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    // Con fetches tan caros (entrenar 2 modelos, ~15-20s), no basta con
    // ignorar la respuesta vieja -- hay que abortar la peticion de verdad,
    // si no el StrictMode de React (monta/desmonta/monta en dev) entrena
    // los modelos DOS VECES en paralelo en cada carga de pantalla.
    return () => {
      controller.abort();
    };
  }, [ticker]);

  const panels = data?.panels ?? [];

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="MACHINE LEARNING · TRAINING"
        subtitle="Weekly candle type (Green/Red) prediction · Model comparison and their most relevant features"
      />
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {!data && !error && (
        <p className="text-sm text-muted-foreground">
          Training models (fixed hyperparameters, no per-ticker search)... first load takes a few seconds.
          Subsequent visits to this ticker are instant (cached).
        </p>
      )}
      {panels.length > 0 && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {panels.map((panel) => (
            <ModelMetricsCard key={panel.model_name} panel={panel} />
          ))}
        </div>
      )}
    </div>
  );
}

export default MLTraining;
