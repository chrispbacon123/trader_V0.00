"""
ML-Powered Trading Strategy with Feature Engineering
Combines technical indicators with gradient boosting for prediction
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score
import warnings
warnings.filterwarnings('ignore')

class MLTradingStrategy:
    def __init__(self, symbol='SPY', initial_capital=100000, lookback=60, prediction_horizon=5):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.lookback = lookback
        self.prediction_horizon = prediction_horizon
        self.model = None
        self.feature_names = []
        self.cash = initial_capital
        self.position = 0
        
    def download_data(self, start_date, end_date):
        """Download historical data - request extra days to account for trading days only"""
        # Add buffer for weekends/holidays (multiply by 1.5 to get enough trading days)
        days_diff = (end_date - start_date).days
        buffer_start = end_date - timedelta(days=int(days_diff * 1.5))
        
        data = yf.download(self.symbol, start=buffer_start, end=end_date, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        return data
    
    def add_features(self, data):
        """Create technical indicators and features - alias for create_features"""
        return self.create_features(data)
    
    def create_features(self, data):
        """Create technical indicators and features"""
        df = data.copy()
        
        # Price-based features
        df['Returns'] = df['Close'].pct_change()
        df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
            df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
            df[f'Price_to_SMA_{period}'] = df['Close'] / df[f'SMA_{period}']
        
        # Volatility
        df['Volatility_20'] = df['Returns'].rolling(window=20).std()
        df['Volatility_50'] = df['Returns'].rolling(window=50).std()
        
        # Momentum indicators
        df['ROC_10'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
        df['ROC_20'] = ((df['Close'] - df['Close'].shift(20)) / df['Close'].shift(20)) * 100
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (2 * bb_std)
        df['BB_Lower'] = df['BB_Middle'] - (2 * bb_std)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # Volume features
        df['Volume_SMA_20'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
        
        # High-Low range
        df['HL_Ratio'] = (df['High'] - df['Low']) / df['Close']
        df['OC_Ratio'] = (df['Open'] - df['Close']) / df['Close']
        
        # Lag features
        for lag in [1, 2, 3, 5]:
            df[f'Return_Lag_{lag}'] = df['Returns'].shift(lag)
        
        # Target: Future return direction
        df['Future_Return'] = df['Close'].shift(-self.prediction_horizon) / df['Close'] - 1
        df['Target'] = (df['Future_Return'] > 0).astype(int)
        
        return df
    
    def prepare_train_test(self, df):
        """Prepare features and target for training"""
        # Select feature columns
        feature_cols = [col for col in df.columns if col not in 
                       ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close',
                        'Future_Return', 'Target', 'Returns', 'Log_Returns']]
        
        # Remove rows with NaN
        df_clean = df[feature_cols + ['Target']].dropna()
        
        X = df_clean[feature_cols]
        y = df_clean['Target']
        
        self.feature_names = feature_cols
        
        return X, y
    
    def train_model(self, X, y, optimize=True):
        """Train XGBoost model with cross-validation"""
        print("\n" + "="*50)
        print("TRAINING ML MODEL")
        print("="*50)
        
        # Validate data size
        if len(X) < 30:
            raise ValueError(f"Insufficient data for training. Need at least 30 samples, got {len(X)}")
        
        # Adaptive number of splits based on data size
        n_splits = min(3, max(2, len(X) // 20))
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        best_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_estimators': 200
        }
        
        # Cross-validation scores
        cv_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            model = xgb.XGBClassifier(**best_params, early_stopping_rounds=20, verbose=0)
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
            
            y_pred = model.predict(X_val)
            accuracy = accuracy_score(y_val, y_pred)
            cv_scores.append(accuracy)
            print(f"Fold {fold+1} Accuracy: {accuracy:.4f}")
        
        print(f"\nMean CV Accuracy: {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores):.4f})")
        
        # Train final model on all data
        self.model = xgb.XGBClassifier(**best_params)
        self.model.fit(X, y)
        
        # Feature importance
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Important Features:")
        print(importance.head(10).to_string(index=False))
        
        return self.model
    
    def generate_signals(self, df):
        """Generate trading signals using trained model"""
        feature_cols = self.feature_names
        X = df[feature_cols]
        
        # Predict probabilities
        df['Prediction_Proba'] = self.model.predict_proba(X)[:, 1]
        df['Prediction'] = (df['Prediction_Proba'] > 0.52).astype(int)  # Slightly higher threshold
        
        # Generate signals: 1 = Buy, -1 = Sell, 0 = Hold
        df['Signal'] = 0
        df.loc[df['Prediction'] == 1, 'Signal'] = 1
        df.loc[df['Prediction'] == 0, 'Signal'] = -1
        
        return df
    
    def backtest(self, start_date, end_date, train_test_split=0.7):
        """Run backtest with train/test split"""
        print("\nDownloading data...")
        data = self.download_data(start_date, end_date)
        
        # Validate data
        if data is None or len(data) == 0:
            raise ValueError(f"No data available for {self.symbol}")
        
        # Need enough trading days - 90 calendar days = ~63 trading days
        min_trading_days = max(60, self.lookback + 20)
        if len(data) < min_trading_days:
            raise ValueError(f"Insufficient data for {self.symbol}. Need at least {min_trading_days} trading days (request 90+ calendar days), got {len(data)}")
        
        print("Creating features...")
        df = self.create_features(data)
        
        print("Preparing dataset...")
        X, y = self.prepare_train_test(df)
        
        if len(X) == 0:
            raise ValueError(f"No valid data after feature creation for {self.symbol}")
        
        # Split into train and test
        split_idx = int(len(X) * train_test_split)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Train model
        self.train_model(X_train, y_train)
        
        # Test set predictions
        test_dates = X_test.index
        df_test = df.loc[test_dates].copy()
        df_test = self.generate_signals(df_test)
        
        # Backtest on test set
        portfolio_value = self.cash
        shares = 0
        trades = []
        equity_curve = []
        
        print("\n" + "="*50)
        print("RUNNING BACKTEST (Test Set)")
        print("="*50)
        
        for date, row in df_test.iterrows():
            if pd.isna(row['Signal']):
                continue
                
            price = row['Close']
            signal = row['Signal']
            
            # Execute trades
            if signal == 1 and shares == 0:  # Buy
                shares = int(self.cash * 0.95 / price)
                cost = shares * price
                self.cash -= cost
                trades.append((date, 'BUY', price, shares, row['Prediction_Proba']))
                
            elif signal == -1 and shares > 0:  # Sell
                proceeds = shares * price
                self.cash += proceeds
                trades.append((date, 'SELL', price, shares, row['Prediction_Proba']))
                shares = 0
            
            # Track portfolio value
            portfolio_value = self.cash + (shares * price)
            equity_curve.append({'Date': date, 'Value': portfolio_value})
        
        # Close any open position
        if shares > 0:
            final_price = df_test['Close'].iloc[-1]
            self.cash += shares * final_price
            portfolio_value = self.cash
        
        return df_test, trades, portfolio_value, equity_curve
    
    def print_results(self, final_value, trades, equity_curve):
        """Print comprehensive backtest results"""
        initial_value = 100000
        total_return = ((final_value - initial_value) / initial_value) * 100
        
        # Calculate metrics
        equity_df = pd.DataFrame(equity_curve)
        equity_df['Returns'] = equity_df['Value'].pct_change()
        
        sharpe_ratio = (equity_df['Returns'].mean() / equity_df['Returns'].std()) * np.sqrt(252)
        max_drawdown = ((equity_df['Value'].cummax() - equity_df['Value']) / equity_df['Value'].cummax()).max() * 100
        
        winning_trades = sum(1 for i in range(0, len(trades)-1, 2) if i+1 < len(trades) and 
                           trades[i+1][2] > trades[i][2])
        total_trade_pairs = len(trades) // 2
        win_rate = (winning_trades / total_trade_pairs * 100) if total_trade_pairs > 0 else 0
        
        print(f"\n{'='*50}")
        print(f"ML STRATEGY RESULTS - {self.symbol}")
        print(f"{'='*50}")
        print(f"Initial Capital: ${initial_value:,.2f}")
        print(f"Final Portfolio Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"Max Drawdown: {max_drawdown:.2f}%")
        print(f"Total Trades: {len(trades)}")
        print(f"Win Rate: {win_rate:.2f}%")
        
        print(f"\nRecent Trades (with ML confidence):")
        for trade in trades[-8:]:
            print(f"  {trade[0].strftime('%Y-%m-%d')} - {trade[1]} {trade[3]} shares @ ${trade[2]:.2f} (conf: {trade[4]:.3f})")

if __name__ == "__main__":
    # Initialize ML strategy
    strategy = MLTradingStrategy(symbol='SPY', lookback=60, prediction_horizon=5)
    
    # Run backtest with longer history for better training
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    df_test, trades, final_value, equity_curve = strategy.backtest(start_date, end_date)
    
    # Print results
    strategy.print_results(final_value, trades, equity_curve)
