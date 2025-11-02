def testing_filters(df, timeframe, start_date, num_sets):
    for index, row in df.iterrows():
        parameter_BullWick = row["P_BullWick"]
        parameter_BearWick = row["P_BearWick"]
        rsiLongTrigger = row["P_RsiLong"] 
        rsiShortTrigger = row["P_RsiShort"] 


def signal_exe():
    markets = kucoin.load_markets() #Load all available markets (contracts)
    symbols = [symbol for symbol in markets if 'USDT' in symbol and markets[symbol]['linear']] # Filter for USDT-margined futures only - # List of symbols to use
    symbols = symbols[:100]
    df = pd.read_csv("filter_trading.csv")

    for symbol in symbols:
        df_symbol = getTradingDataFrame(symbol)
        last_candle = df.iloc[:-1]
        row = df[df["symbol"] == symbol]

        if (last_candle["rsi"] >= row["P_RsiShort"]) and ((last_candle["upper_wick"] / last_candle["candle_range"]) >= row["BearWick"]):
            print("Short: " + symbol)        
        elif (last_candle["rsi"] <= row["P_RsiLong"]) and ((last_candle["lower_wick"] / last_candle["candle_range"]) >= row["BullWick"]):
            print("Long: " + symbol) 


    with ProcessPoolExecutor(max_workers=10) as executor:
        dataframes = list(executor.map(getTradingDataFrame, symbols))