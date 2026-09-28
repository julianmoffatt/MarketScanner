from scipy.stats import percentileofscore
import numpy as np
import pandas as pd


def _time_away_running(df, ema_col, weight=0.3, vol_window=20):
    log_returns = np.log(df["Close"] / df["Close"].shift(1))
    vol = log_returns.rolling(vol_window).std() * 100

    vol_p20 = vol.expanding().quantile(0.20)
    vol_p80 = vol.expanding().quantile(0.80)
    tolerance = (vol.fillna(vol_p20).clip(vol_p20, vol_p80) / 100) * weight

    ema = df[ema_col]
    is_away = ((df["Low"] * (1 - tolerance)) > ema) | ((df["High"] * (1 + tolerance)) < ema)

    groups = (is_away != is_away.shift()).cumsum()
    streak = is_away.groupby(groups).cumcount() + 1
    return streak.where(is_away, 0)


def _streak_running(df):
    is_green = df["type"] == "Green"
    groups = (is_green != is_green.shift()).cumsum()
    return is_green.groupby(groups).cumcount() + 1


def _position_vs_period_open(df, freq):
    period = df["date"].dt.to_period(freq)
    period_open = df.groupby(period)["Open"].transform("first")
    return (df["Close"] - period_open) / period_open * 100


def _period_strike(df, freq):
    # Racha de periodos (mes/trimestre/año) COMPLETOS consecutivos del mismo
    # color -- mismo criterio que "type" en las velas normales (Close vs
    # Close del periodo anterior, no vs su propio Open). shift(1) al final
    # es clave para no usar el color del periodo AUN EN CURSO: toda semana
    # dentro de un mes en marcha ve la racha tal como quedo al CERRAR el
    # mes anterior, no una que dependa de como termine el mes actual (eso
    # si seria mirar al futuro).
    period = df["date"].dt.to_period(freq)
    period_close = df.groupby(period)["Close"].last()
    is_green = period_close > period_close.shift(1)
    groups = (is_green != is_green.shift()).cumsum()
    period_streak = is_green.groupby(groups).cumcount() + 1
    return period.map(period_streak.shift(1))


def _dist_to_prev_year_extreme(df, col, agg):
    # High/Low del año natural ANTERIOR completo -- sin look-ahead: para
    # cualquier semana del año Y, el año Y-1 ya esta cerrado del todo, asi
    # que su High/Low maximo/minimo ya es un dato conocido de antemano, no
    # una fuga de informacion futura (distinto de agrupar por el año EN
    # CURSO, que si seria una vela "viendo" su propio futuro dentro del año).
    year = df["date"].dt.year
    yearly_extreme = df.groupby(year)[col].agg(agg)
    prev_year_extreme = yearly_extreme.reindex(year - 1).values
    return (df["Close"] - prev_year_extreme) / prev_year_extreme * 100


def add_macro_rate_features(weekly, tnx_weekly, irx_weekly):
    """
    Tipos de interes (10Y treasury yield, 3-month T-bill yield) y su spread,
    como contexto macro compartido por TODOS los tickers (no se deriva del
    propio activo, es el mismo valor esa semana para cualquiera).

    Sin look-ahead: tnx_weekly/irx_weekly ya vienen resampleados a semanal
    con el mismo anclaje 'W-MON' que el df objetivo, asi que emparejar por
    la MISMA semana es tan valido como usar el propio Close semanal del
    activo -- ambos son datos ya cerrados de esa semana, no del futuro.
    A diferencia del intento anterior con datos diarios/mensuales, aqui no
    hace falta ningun shift de periodo: no hay timeframes de distinta
    granularidad de por medio.

    Percentil para los niveles (tnx/irx) -- igual que rsi_percentile, "es
    alto/bajo para su epoca" importa mas que el numero crudo, y los tipos
    de interes tienen regimenes largos (cerca de cero en 2010s, mucho mas
    altos despues) que hacen el nivel crudo poco comparable entre epocas.
    Crudo para el spread -- una inversion (spread negativo) es un umbral
    economico absoluto, no relativo a su propia historia.

    (Se probo tambien añadir petroleo y dolar, como extension al EMA, y
    despues el VIX como percentil de nivel -- ambos daban una pequeña
    mejora media en el universo de indices/commodities/forex, pero
    empeoraban notablemente el resultado en SP500 y NASDAQ especificamente,
    los dos tickers de referencia de este proyecto (en el caso del VIX,
    sobre todo en RandomForest: -0.064 AUC en SP500, -0.035 en NASDAQ).
    Se revirtieron ambos: no vale la pena una mejora media a costa de los
    dos casos que mas importan.)
    """
    tnx_close = tnx_weekly.set_index("date")["Close"]
    irx_close = irx_weekly.set_index("date")["Close"]

    tnx_pct = pd.Series(
        [percentileofscore(tnx_close.iloc[:i].dropna(), tnx_close.iloc[i], kind="rank") for i in range(len(tnx_close))],
        index=tnx_close.index,
    )
    irx_pct = pd.Series(
        [percentileofscore(irx_close.iloc[:i].dropna(), irx_close.iloc[i], kind="rank") for i in range(len(irx_close))],
        index=irx_close.index,
    )
    spread = tnx_close - irx_close

    dates = weekly["date"]
    result = pd.DataFrame({
        "tnx_percentile": tnx_pct.reindex(dates).values,
        "irx_percentile": irx_pct.reindex(dates).values,
        "yield_spread": spread.reindex(dates).values,
    })
    result.index = weekly.index
    return result


MIN_HISTORY_ROWS = 300  # por debajo de esto ni se intenta: no da ni para un
                         # warm-up + split 80/20 + TimeSeriesSplit(5) razonable
                         # (ej. una IPO reciente como RDDT, ~589 velas, ya se
                         # queda corta para el SHORT_WINDOW=1000 fijo -- confirmado
                         # con un IndexError real al pedir X_latest sobre un df vacio)


def build_features_ML(df, tnx_weekly, irx_weekly):
    if len(df) < MIN_HISTORY_ROWS:
        raise ValueError(
            f"Solo hay {len(df)} velas de historico -- hacen falta al menos "
            f"{MIN_HISTORY_ROWS} para entrenar un modelo con garantias "
            f"(activo probablemente demasiado reciente, ej. una IPO reciente)."
        )

    # Handling look ahead bias features
    df = df.drop('next_close', axis=1) 
    df = df.drop('return_next_day', axis=1)
    # Creating calendar info features
    # Sin day_of_week: en velas semanales seria una constante (siempre el
    # mismo dia de anclaje del resample), cero informacion. day_of_month pasa
    # a ser el dia del mes en el que EMPIEZA esa semana (preprocessing.py
    # resamplea con label="left", asi que "date" ya es el primer dia de la
    # semana, no hace falta recalcular nada, solo dejar claro que significa).
    df["week_start_day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter  
    df["week_of_year"] = df["date"].dt.isocalendar().week 
    # Creating advanced features
    # - rsi
    df["rsi_percentile"] = [percentileofscore(df["rsi"].iloc[:i].dropna(), df["rsi"].iloc[i], kind="rank") for i in range(len(df))]
    df = df.drop('rsi', axis=1)
    # - distance to mean
    ema_extensions = ["extension_ema10", "extension_ema20", "extension_ema50", "extension_ema200"]
    # Objetivo 5 años (260 semanas) como ventana "reciente" estandar --
    # antes escalaba hasta 1000 filas (~19 años) o un tercio del historico,
    # lo que en tickers con mucha historia (SP500 con la excepcion de 64
    # años, por ejemplo) tiraba mas de una decada de warm-up sin necesidad
    # real: 520 puntos ya dan de sobra para que percentileofscore no sea
    # ruido. Ademas, un valor FIJO (no escalado por ticker) hace que la
    # ventana de "regimen reciente" signifique lo mismo para todos los
    # activos, algo mas homogeneo y comparable entre tickers que antes.
    # Se sigue topando a un tercio del historico disponible para no dejar
    # el dataset vacio en activos mas recientes -- ya paso MIN_HISTORY_ROWS
    # arriba, asi que siempre queda margen para train/test despues del
    # warm-up.
    SHORT_WINDOW = min(5 * 52, len(df) // 3)
    # percentileofscore devuelve NaN para TODA la llamada si el array de
    # comparacion contiene un solo NaN (confirmado, no solo para el score en
    # si) -- con activos que tienen alguna semana sin operaciones (futuros
    # poco liquidos como platino/paladio, o gaps de reporting en forex), el
    # resample deja esa semana entera en NaN, y sin dropar eso del historico
    # esa unica fila NaN se contagia a CASI TODAS las percentiles siguientes
    # (confirmado: 1433 de 1499 filas NaN en PLATINUM). Por eso todo
    # percentileofscore de aqui en adelante limpia el historico con
    # .dropna() antes de comparar, igual que ya se hacia con rsi_percentile.
    for ema_extension in ema_extensions:
        df["percentile_"+ema_extension] = [percentileofscore(df[ema_extension].iloc[:i].dropna(), df[ema_extension].iloc[i], kind="rank") for i in range(len(df))]
        # corto / régimen reciente (rolling ventana fija)
        col = df[ema_extension]
        df["percentile_short_" + ema_extension] = [
            percentileofscore(col.iloc[i - SHORT_WINDOW:i].dropna(), col.iloc[i], kind="rank")
            if i >= SHORT_WINDOW else np.nan
            for i in range(len(df))
        ]
    # - time away from mean
    ema_periods = [10, 20, 50, 200]
    for ema_period in ema_periods:
        col_name = "time_away_ema" + str(ema_period)
        df[col_name] = _time_away_running(df, "ema" + str(ema_period))
        col = df[col_name]
        df["percentile_" + col_name] = [
            percentileofscore(col.iloc[:i].dropna(), col.iloc[i], kind="rank") for i in range(len(df))
        ]
    # - position respect open
    # Sin "week": esta funcion solo se llama sobre velas ya semanales, y ahi
    # agrupar por semana da un grupo de una sola fila -- el "open de la
    # semana" séria el propio Open de esa misma vela, redundante con "return".
    # month/quarter/year si siguen siendo periodos genuinamente mas grandes
    # que una semana, asi que ahi la comparacion sigue aportando informacion.
    period_freqs = {"month": "M", "quarter": "Q", "year": "Y"}
    for label, freq in period_freqs.items():
        df["position_vs_" + label + "_open"] = _position_vs_period_open(df, freq)

    # - distancia al maximo/minimo del año natural anterior: zona de
    # inflexion clasica (soporte/resistencia) donde el precio suele
    # reaccionar al acercarse o cruzarla. En % de Close, igual que las
    # extension_ema*, no un simple si/no -- asi el modelo conserva la
    # magnitud (cuan lejos) y no solo el signo (por encima/por debajo).
    df["dist_to_prev_year_high"] = _dist_to_prev_year_extreme(df, "High", "max")
    df["dist_to_prev_year_low"] = _dist_to_prev_year_extreme(df, "Low", "min")

    # - mechas de velas anteriores: una absorcion (rechazo de precio marcado
    # por una mecha larga) en velas semanales a veces no se resuelve en una
    # sola vela, tarda 2-3 velas en confirmarse -- el modelo necesita ver
    # tambien las mechas de las 1-2 velas previas, no solo la actual.
    for lag in [1, 2]:
        df[f"upper_wick_lag{lag}"] = df["upper_wick"].shift(lag)
        df[f"lower_wick_lag{lag}"] = df["lower_wick"].shift(lag)


    # - strikes (racha de velas seguidas del mismo color)
    df["streak"] = _streak_running(df)
    df["percentile_streak"] = [
        percentileofscore(df["streak"].iloc[:i].dropna(), df["streak"].iloc[i], kind="rank") for i in range(len(df))
    ]

    # - strikes de periodos mas largos: no solo rachas de velas semanales,
    # tambien de meses/trimestres/años COMPLETOS consecutivos del mismo
    # color (ver _period_strike para el detalle del shift anti-look-ahead).
    period_strike_freqs = {"month": "M", "quarter": "Q", "year": "Y"}
    for label, freq in period_strike_freqs.items():
        col_name = label + "_strike"
        df[col_name] = _period_strike(df, freq)
        df["percentile_" + col_name] = [
            percentileofscore(df[col_name].iloc[:i].dropna(), df[col_name].iloc[i], kind="rank") for i in range(len(df))
        ]

    # - tipos de interes (10Y, 3-month, spread): contexto macro, ver
    # add_macro_rate_features para el detalle de por que no hace falta
    # shift de periodo aqui (todo ya esta a granularidad semanal).
    macro = add_macro_rate_features(df, tnx_weekly, irx_weekly)
    df = pd.concat([df, macro], axis=1)

    # Deleting features no estacionarios
    # "Adj Close" solo existe en velas diarias (viene del dato crudo de
    # origen) -- las semanales/mensuales/etc. se construyen con resample()
    # agregando solo Open/High/Low/Close/Volume, asi que no la tienen.
    raw_price_cols = ["date", "Adj Close", "Open", "High", "Low", "Close", "Volume",
                       "last_close", "ema10", "ema20", "ema50", "ema200"]
    df = df.drop(columns=[c for c in raw_price_cols if c in df.columns])

    # Deleting some time that can confuse the model with percentiles without warming up
    df = df.iloc[SHORT_WINDOW:].copy()

    # creating target variable y
    df["y_type"] = df["type"].shift(-1)

    # La ultima fila es "hoy": no tiene y_type (no sabemos aun el tipo de
    # manana), por eso el dropna() de abajo la descarta del set de
    # entrenamiento -- pero es justo la fila que hace falta para predecir en
    # vivo, asi que la guardamos aparte antes de perderla.
    X_latest = df.drop(columns=["y_type"]).iloc[[-1]]

    df = df.dropna()
    X = df.drop('y_type', axis=1)
    y = df['y_type']
    return X, y, X_latest