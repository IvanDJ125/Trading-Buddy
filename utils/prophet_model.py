import os
import sys

# Add the project root directory to sys.path
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

from prophet import Prophet
from utils.stock_data import get_stock_data
import plotly.graph_objects as go

def predict_and_plot_prophet(ticker, forecast_period=30):
    """
    Use the Prophet model to predict stock prices and plot the results.

    Args:
        ticker (str): Stock ticker symbol.
        forecast_period (int): Number of days to forecast (default is 30).

    Returns:
        dict: A summary of the forecast, including the latest predicted price.
        plotly.graph_objects.Figure: A Plotly figure object for the prediction plot.
    """
    try:
        # Fetch historical stock data (defaults to 5y period and 1d interval)
        data = get_stock_data(ticker)

        if data is None or 'Close' not in data:
            return {"error": "Failed to fetch stock data or invalid data format."}, None

        # Reset index to make the date a column and rename columns for Prophet
        data = data.reset_index()  # Reset index to make date column explicit
        data.rename(columns={'index': 'Date'}, inplace=True)  # Ensure the date column is named 'Date'
        prophet_data = data[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})

        # Initialize and fit the Prophet model
        model = Prophet()
        model.fit(prophet_data)

        # Create a DataFrame for future dates
        future = model.make_future_dataframe(periods=forecast_period)
        forecast = model.predict(future)

        # Create Plotly figure
        fig = go.Figure()

        # Plot historical closing prices
        fig.add_trace(go.Scatter(
            x=prophet_data['ds'],
            y=prophet_data['y'],
            mode='lines',
            name='Historical Closing Prices',
            line=dict(color='blue')
        ))

        # Plot predicted prices
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat'],
            mode='lines',
            name='Predicted Prices',
            line=dict(color='green')
        ))

        # Plot confidence intervals
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat_upper'],
            mode='lines',
            name='Upper Confidence Interval',
            line=dict(dash='dot', color='green')
        ))

        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat_lower'],
            mode='lines',
            name='Lower Confidence Interval',
            line=dict(dash='dot', color='green')
        ))

        # Customize layout
        fig.update_layout(
            title=f"{ticker.upper()} Stock Price Prediction (Prophet)",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            xaxis_rangeslider_visible=True
        )

        # Get the latest prediction
        latest_forecast = forecast[['ds', 'yhat']].iloc[-1]
        latest_predicted_price = latest_forecast['yhat']
        latest_date = latest_forecast['ds']

        # Compare the latest predicted price with the most recent historical price
        last_historical_price = prophet_data['y'].iloc[-1]

        # Determine if the stock is projected to go up or down
        if latest_predicted_price > last_historical_price:
            prediction_message = "In the next 60 days, the stock price is projected to go up."
        else:
            prediction_message = "In the next 60 days, the stock price is projected to go down."

        # Return the message and figure
        return {
            "prediction_message": prediction_message,
            "latest_date": latest_date
        }, fig

    except Exception as e:
        return {"error": str(e)}, None

