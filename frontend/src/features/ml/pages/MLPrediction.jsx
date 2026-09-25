import { useEffect, useState } from "react";
import { useTicker } from "../../analytics/hooks/useTicker";
import { getMLPrediction } from "../api/mlApi";
import ScreenHeader from "../../analytics/components/ScreenHeader";
import PredictionCard from "../components/PredictionCard";

function MLPrediction() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    setData(null);
    getMLPrediction(ticker, { signal: controller.signal })
      .then((result) => {
        setData(result);
      })
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    // Ver comentario en MLTraining.jsx: hay que abortar de verdad, no solo
    // ignorar la respuesta vieja, o el StrictMode de React duplica el
    // entrenamiento en el backend en cada carga de pantalla.
    return () => {
      controller.abort();
    };
  }, [ticker]);

  const panels = data?.panels ?? [];

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="MACHINE LEARNING · PREDICTION"
        subtitle={
          data
            ? `Prediccion para la vela siguiente a ${data.as_of_date.slice(0, 10)}`
            : "Prediccion en vivo del tipo de vela (Green/Red) del dia siguiente"
        }
      />
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {!data && !error && (
        <p className="text-sm text-muted-foreground">
          Entrenando modelos (GridSearchCV + TimeSeriesSplit)... puede tardar desde unos segundos hasta un par de
          minutos en tickers con mucho historico. Los siguientes accesos a este ticker son instantaneos (cache).
        </p>
      )}
      {panels.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {panels.map((panel) => (
              <PredictionCard key={panel.model_name} panel={panel} />
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Ilustrativo, no es una recomendacion de inversion.
          </p>
        </>
      )}
    </div>
  );
}

export default MLPrediction;
