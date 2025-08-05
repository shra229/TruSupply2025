from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import plotly.graph_objs as go
import plotly  # ✅ Required for Plotly JSON encoding
import json
from datetime import datetime
import os

app = Flask(__name__)
DATA_FILE = 'supplier_data.xlsx'

# Helper function to calculate risk score and level
def calculate_risk(financial, quality, delivery, sustainability, compliance):
    scores = [financial, quality, delivery, sustainability, compliance]
    valid_scores = [s for s in scores if pd.notnull(s)]
    if not valid_scores:
        return 0, "Low Risk"
    risk_score = round(sum(valid_scores) / len(valid_scores), 2)
    if risk_score <= 44:
        level = "Low Risk"
    elif 45 <= risk_score <= 65:
        level = "Medium Risk"
    else:
        level = "High Risk"
    return risk_score, level

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate_supplier', methods=['GET', 'POST'])
def evaluate_supplier():
    if request.method == 'POST':
        supplier_name = request.form['supplier_name']
        financial_score = float(request.form['financial_score'])
        quality_score = float(request.form['quality_score'])
        delivery_score = float(request.form['delivery_score'])
        sustainability_score = float(request.form['sustainability_score'])
        compliance_score = float(request.form['compliance_score'])

        risk_score, risk_level = calculate_risk(
            financial_score,
            quality_score,
            delivery_score,
            sustainability_score,
            compliance_score
        )

        evaluation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Create new row
        new_data = {
            'Supplier Name': supplier_name,
            'Financial Score': financial_score,
            'Quality Score': quality_score,
            'Delivery Score': delivery_score,
            'Sustainability Score': sustainability_score,
            'Compliance Score': compliance_score,
            'Risk Score': risk_score,
            'Risk Level': risk_level,
            'Evaluation Date': evaluation_date
        }

        # Save to Excel
        if os.path.exists(DATA_FILE):
            df = pd.read_excel(DATA_FILE)
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        else:
            df = pd.DataFrame([new_data])
        df.to_excel(DATA_FILE, index=False)

        # Create charts (for this supplier only)
        pie = go.Figure(data=[go.Pie(
            labels=['Financial', 'Quality', 'Delivery', 'Sustainability', 'Compliance'],
            values=[financial_score, quality_score, delivery_score, sustainability_score, compliance_score]
        )])
        pie.update_layout(title='Supplier Score Distribution')

        bar = go.Figure(data=[go.Bar(
            x=['Financial', 'Quality', 'Delivery', 'Sustainability', 'Compliance'],
            y=[financial_score, quality_score, delivery_score, sustainability_score, compliance_score]
        )])
        bar.update_layout(title='Supplier Score Breakdown')

        pieJSON = json.dumps(pie, cls=plotly.utils.PlotlyJSONEncoder)
        barJSON = json.dumps(bar, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('form.html',
                               supplier_name=supplier_name,
                               risk_score=risk_score,
                               risk_level=risk_level,
                               pieJSON=pieJSON,
                               barJSON=barJSON)
    return render_template('form.html')

@app.route('/dashboard')
def dashboard():
    if not os.path.exists(DATA_FILE):
        return render_template('dashboard.html', no_data=True)

    df = pd.read_excel(DATA_FILE)

    pie = go.Figure(data=[go.Pie(
        labels=df['Risk Level'].value_counts().index,
        values=df['Risk Level'].value_counts().values
    )])
    pie.update_layout(title='Risk Level Distribution')

    bar = go.Figure(data=[go.Bar(
        x=df['Supplier Name'],
        y=df['Risk Score'],
        name='Risk Score'
    )])
    bar.update_layout(title='Supplier Risk Scores', xaxis_title='Supplier', yaxis_title='Risk Score')

    line = go.Figure()
    df['Evaluation Date'] = pd.to_datetime(df['Evaluation Date'])
    df_sorted = df.sort_values('Evaluation Date')
    line.add_trace(go.Scatter(
        x=df_sorted['Evaluation Date'],
        y=df_sorted['Risk Score'],
        mode='lines+markers',
        name='Risk Over Time'
    ))
    line.update_layout(title='Risk Score Over Time')

    pieJSON = json.dumps(pie, cls=plotly.utils.PlotlyJSONEncoder)
    barJSON = json.dumps(bar, cls=plotly.utils.PlotlyJSONEncoder)
    lineJSON = json.dumps(line, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('dashboard.html',
                           pieJSON=pieJSON,
                           barJSON=barJSON,
                           lineJSON=lineJSON)

@app.route('/view_history')
def view_history():
    if not os.path.exists(DATA_FILE):
        return render_template('view_history.html', data=[])
    df = pd.read_excel(DATA_FILE)
    df = df[['Supplier Name', 'Financial Score', 'Quality Score', 'Delivery Score',
             'Sustainability Score', 'Compliance Score', 'Risk Score', 'Risk Level', 'Evaluation Date']]
    df = df.dropna(how='all')  # Remove empty rows
    data = df.to_dict(orient='records')
    return render_template('view_history.html', data=data)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        return redirect(url_for('thankyou'))
    return render_template('feedback.html')

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

if __name__ == '__main__':
    app.run(debug=True)
