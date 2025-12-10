"""
Optimized ML Trading Strategy with Hyperparameter Tuning
Uses Optuna for automatic optimization and ensemble models
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score
import optuna
import warnings
warnings.filterwarnings('ignore')

class OptimizedMLStrategy:
    def __init__(self, symbol='SPY', initial_capital=100000, lookback=60, prediction_horizon=5):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.lookback = lookback
        self.prediction_horizon = prediction_horizon
        self.models = {}
        self.feature_names = []
        self.cash = initial_capital
        self.initial_cash = initial_capital
        self.best_params = None
        
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
        """Create comprehensive technical indicators - alias for create_features"""
        return self.create_features(data)
    
    def create_features(self, data):
        """Create comprehensive technical indicators"""
        df = data.copy()
        
        # Returns and momentum
        df['Returns'] = df['Close'].pct_change()
        df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Multiple timeframe moving averages
        for period in [5, 10, 20, 50, 100, 200]:
            df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
            df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
            df[f'Price_to_SMA_{period}'] = df['Close'] / df[f'SMA_{period}']
        
        # Volatility metrics
        for period in [10, 20, 50]:
            df[f'Volatility_{period}'] = df['Returns'].rolling(window=period).std()
            df[f'ATR_{period}'] = (df['High'] - df['Low']).rolling(window=period).mean()
        
        # Rate of Change
        for period in [5, 10, 20, 30]:
            df[f'ROC_{period}'] = ((df['Close'] - df['Close'].shift(period)) / df['Close'].shift(period)) * 100
        
        # RSI for multiple periods
        for period in [7, 14, 21]:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'RSI_{period}'] = 100 - (100 / (1 + rs))
        
        # MACD variations
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Bollinger Bands
        for period in [10, 20, 50]:
            bb_middle = df['Close'].rolling(window=period).mean()
            bb_std = df['Close'].rolling(window=period).std()
            df[f'BB_Upper_{period}'] = bb_middle + (2 * bb_std)
            df[f'BB_Lower_{period}'] = bb_middle - (2 * bb_std)
            df[f'BB_Width_{period}'] = (df[f'BB_Upper_{period}'] - df[f'BB_Lower_{period}']) / bb_middle
            df[f'BB_Position_{period}'] = (df['Close'] - df[f'BB_Lower_{period}']) / (df[f'BB_Upper_{period}'] - df[f'BB_Lower_{period}'])
        
        # Volume analysis
        df['Volume_SMA_20'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
        df['OBV_EMA'] = df['OBV'].ewm(span=20).mean()
        
        # Price patterns
        df['HL_Ratio'] = (df['High'] - df['Low']) / df['Close']
        df['OC_Ratio'] = (df['Open'] - df['Close']) / df['Close']
        df['Upper_Shadow'] = (df['High'] - np.maximum(df['Open'], df['Close'])) / df['Close']
        df['Lower_Shadow'] = (np.minimum(df['Open'], df['Close']) - df['Low']) / df['Close']
        
        # Lag features
        for lag in [1, 2, 3, 5, 10]:
            df[f'Return_Lag_{lag}'] = df['Returns'].shift(lag)
            df[f'Volume_Lag_{lag}'] = df['Volume_Ratio'].shift(lag)
        
        # Rolling statistics
        df['Return_Mean_20'] = df['Returns'].rolling(window=20).mean()
        df['Return_Std_20'] = df['Returns'].rolling(window=20).std()
        df['Return_Skew_20'] = df['Returns'].rolling(window=20).skew()
        df['Return_Kurt_20'] = df['Returns'].rolling(window=20).kurt()
        
        # Target
        df['Future_Return'] = df['Close'].shift(-self.prediction_horizon) / df['Close'] - 1
        df['Target'] = (df['Future_Return'] > 0.001).astype(int)  # Small threshold to avoid noise
        
        return df
    
    def prepare_data(self, df):
        """Prepare features and target"""
        feature_cols = [col for col in df.columns if col not in 
                       ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close',
                        'Future_Return', 'Target', 'Returns', 'Log_Returns', 'OBV']]
        
        df_clean = df[feature_cols + ['Target']].dropna()
        X = df_clean[feature_cols]
        y = df_clean['Target']
        self.feature_names = feature_cols
        
        return X, y
    
    def objective(self, trial, X_train, y_train):
        """Optuna objective function for hyperparameter optimization"""
        params = {
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'gamma': trial.suggest_float('gamma', 0, 5),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 2),
            'reg_lambda': trial.suggest_float('reg_lambda', 0, 2),
        }
        
        # Adaptive splits based on data size
        n_splits = min(3, max(2, len(X_train) // 50))
        tscv = TimeSeriesSplit(n_splits=n_splits)
        scores = []
        
        for train_idx, val_idx in tscv.split(X_train):
            X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
            
            model = xgb.XGBClassifier(**params, objective='binary:logistic', 
                                     random_state=42, eval_metric='logloss',
                                     early_stopping_rounds=20)
            model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
            
            y_pred = model.predict(X_val)
            score = precision_score(y_val, y_pred, zero_division=0)
            scores.append(score)
        
        return np.mean(scores)
    
    def optimize_hyperparameters(self, X_train, y_train, n_trials=30):
        """Optimize hyperparameters using Optuna"""
        print("\n" + "="*50)
        print("OPTIMIZING HYPERPARAMETERS")
        print("="*50)
        
        study = optuna.create_study(direction='maximize', 
                                   sampler=optuna.samplers.TPESampler(seed=42))
        study.optimize(lambda trial: self.objective(trial, X_train, y_train), 
                      n_trials=n_trials, show_progress_bar=False)
        
        self.best_params = study.best_params
        print(f"Best Precision Score: {study.best_value:.4f}")
        print(f"\nBest Parameters:")
        for key, value in self.best_params.items():
            print(f"  {key}: {value}")
        
        return self.best_params
    
    def train_ensemble(self, X_train, y_train):
        """Train ensemble of models"""
        print("\n" + "="*50)
        print("TRAINING ENSEMBLE MODELS")
        print("="*50)
        
        # XGBoost with optimized params
        xgb_params = {**self.best_params, 
                     'objective': 'binary:logistic',
                     'random_state': 42}
        self.models['xgboost'] = xgb.XGBClassifier(**xgb_params)
        self.models['xgboost'].fit(X_train, y_train)
        print("✓ XGBoost trained")
        
        # Random Forest
        self.models['rf'] = RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_split=5,
            random_state=42, n_jobs=-1
        )
        self.models['rf'].fit(X_train, y_train)
        print("✓ Random Forest trained")
        
        # Gradient Boosting
        self.models['gb'] = GradientBoostingClassifier(
            n_estimators=150, max_depth=5, learning_rate=0.1,
            random_state=42
        )
        self.models['gb'].fit(X_train, y_train)
        print("✓ Gradient Boosting trained")
        
        return self.models
    
    def predict_ensemble(self, X):
        """Make predictions using ensemble voting"""
        predictions = np.zeros((len(X), len(self.models)))
        
        for idx, (name, model) in enumerate(self.models.items()):
            if hasattr(model, 'predict_proba'):
                predictions[:, idx] = model.predict_proba(X)[:, 1]
            else:
                predictions[:, idx] = model.predict(X)
        
        # Weighted average (XGBoost gets higher weight)
        weights = np.array([0.5, 0.25, 0.25])  # XGBoost, RF, GB
        ensemble_proba = np.average(predictions, axis=1, weights=weights)
        
        return ensemble_proba
    
    def backtest(self, start_date, end_date, optimize_params=True, n_trials=30):
        """Run optimized backtest"""
        print("\nDownloading data...")
        data = self.download_data(start_date, end_date)
        
        # Validate data
        if data is None or len(data) == 0:
            raise ValueError(f"No data available for {self.symbol}")
        
        # Need enough trading days - 120 calendar days = ~84 trading days
        min_trading_days = max(80, self.lookback + 40)
        if len(data) < min_trading_days:
            raise ValueError(f"Insufficient data for {self.symbol}. Need at least {min_trading_days} trading days (request 120+ calendar days), got {len(data)}")
        
        print("Creating features...")
        df = self.create_features(data)
        
        print("Preparing dataset...")
        X, y = self.prepare_data(df)
        
        if len(X) < 40:
            raise ValueError(f"Insufficient valid data after processing. Need at least 40 samples (requires 250+ calendar days), got {len(X)}")
        
        # Train/test split (70/30)
        split_idx = int(len(X) * 0.7)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Optimize hyperparameters
        if optimize_params:
            self.optimize_hyperparameters(X_train, y_train, n_trials=n_trials)
        else:
            self.best_params = {
                'max_depth': 6, 'learning_rate': 0.05, 'n_estimators': 200,
                'subsample': 0.8, 'colsample_bytree': 0.8
            }
        
        # Train ensemble
        self.train_ensemble(X_train, y_train)
        
        # Generate predictions on test set
        test_dates = X_test.index
        df_test = df.loc[test_dates].copy()
        df_test['Ensemble_Proba'] = self.predict_ensemble(X_test)
        df_test['Prediction'] = (df_test['Ensemble_Proba'] > 0.55).astype(int)
        
        # Backtest
        trades = []
        equity_curve = []
        shares = 0
        
        print("\n" + "="*50)
        print("RUNNING BACKTEST")
        print("="*50)
        
        for date, row in df_test.iterrows():
            if pd.isna(row['Prediction']):
                continue
                
            price = row['Close']
            confidence = row['Ensemble_Proba']
            
            # Dynamic position sizing based on confidence
            position_size = min(0.95, 0.5 + (confidence - 0.5))
            
            # Buy signal
            if row['Prediction'] == 1 and shares == 0 and confidence > 0.55:
                shares = int(self.cash * position_size / price)
                cost = shares * price
                self.cash -= cost
                trades.append((date, 'BUY', price, shares, confidence))
                
            # Sell signal
            elif (row['Prediction'] == 0 or confidence < 0.45) and shares > 0:
                proceeds = shares * price
                self.cash += proceeds
                trades.append((date, 'SELL', price, shares, confidence))
                shares = 0
            
            # Track portfolio
            portfolio_value = self.cash + (shares * price)
            equity_curve.append({'Date': date, 'Value': portfolio_value})
        
        # Close final position
        if shares > 0:
            final_price = df_test['Close'].iloc[-1]
            self.cash += shares * final_price
        
        final_value = self.cash
        
        return df_test, trades, final_value, equity_curve
    
    def print_results(self, final_value, trades, equity_curve):
        """Print comprehensive results"""
        total_return = ((final_value - self.initial_cash) / self.initial_cash) * 100
        
        equity_df = pd.DataFrame(equity_curve)
        if len(equity_df) > 1:
            equity_df['Returns'] = equity_df['Value'].pct_change()
            sharpe = (equity_df['Returns'].mean() / equity_df['Returns'].std()) * np.sqrt(252)
            max_dd = ((equity_df['Value'].cummax() - equity_df['Value']) / equity_df['Value'].cummax()).max() * 100
        else:
            sharpe, max_dd = 0, 0
        
        wins = sum(1 for i in range(0, len(trades)-1, 2) 
                  if i+1 < len(trades) and trades[i+1][2] > trades[i][2])
        total_pairs = len(trades) // 2
        win_rate = (wins / total_pairs * 100) if total_pairs > 0 else 0
        
        print(f"\n{'='*50}")
        print(f"OPTIMIZED ML STRATEGY - {self.symbol}")
        print(f"{'='*50}")
        print(f"Initial Capital: ${self.initial_cash:,.2f}")
        print(f"Final Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Sharpe Ratio: {sharpe:.2f}")
        print(f"Max Drawdown: {max_dd:.2f}%")
        print(f"Total Trades: {len(trades)}")
        print(f"Win Rate: {win_rate:.2f}%")
        
        if len(trades) >= 8:
            print(f"\nRecent Trades:")
            for trade in trades[-8:]:
                print(f"  {trade[0].strftime('%Y-%m-%d')} {trade[1]:4s} {trade[3]:3d} shares @ ${trade[2]:7.2f} (conf: {trade[4]:.3f})")

if __name__ == "__main__":
    strategy = OptimizedMLStrategy(symbol='SPY', lookback=60, prediction_horizon=5)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    df_test, trades, final_value, equity = strategy.backtest(
        start_date, end_date, optimize_params=True, n_trials=20
    )
    
    strategy.print_results(final_value, trades, equity)
