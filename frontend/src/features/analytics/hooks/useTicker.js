import { useNavigate, useParams, useLocation } from "react-router-dom";

// El ticker vive en la URL (/analytics/:ticker/...), no en estado local --
// asi cualquier pantalla lo lee del mismo lugar y un link a un analisis
// puntual es compartible/bookmarkeable.
export function useTicker() {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const setTicker = (newTicker) => {
    // El primer segmento (analytics/ml) no se hardcodea -- asi este hook
    // sirve igual para /analytics/:ticker/... y /ml/:ticker/...
    const [, section, , screen] = location.pathname.split("/");
    navigate(`/${section}/${newTicker}/${screen}${location.search}`);
  };

  return { ticker, setTicker };
}
