import { useNavigate, useParams, useLocation } from "react-router-dom";

// El ticker vive en la URL (/analytics/:ticker/...), no en estado local --
// asi cualquier pantalla lo lee del mismo lugar y un link a un analisis
// puntual es compartible/bookmarkeable.
export function useTicker() {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const setTicker = (newTicker) => {
    const screen = location.pathname.split("/").pop();
    navigate(`/analytics/${newTicker}/${screen}${location.search}`);
  };

  return { ticker, setTicker };
}
