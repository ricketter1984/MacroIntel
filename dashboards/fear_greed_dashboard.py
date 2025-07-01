import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
FEAR_GREED_API_KEY = os.getenv("FEAR_GREED_API_KEY")
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Data Fetching ---
def get_fear_greed_report():
    """
    Fetch the CNN Fear & Greed Index data.
    Returns a dict with score, rating, and historical data.
    """
    url = "https://cnn-fear-and-greed-index.p.rapidapi.com/cnn/v1/fear_and_greed/index"
    headers = {
        "x-rapidapi-key": os.getenv("FEAR_GREED_API_KEY"),
        "x-rapidapi-host": "cnn-fear-and-greed-index.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            index_data = data.get("data", {})
            return {
                "score": float(index_data.get("score", 0)),
                "rating": index_data.get("rating", "Neutral"),
                "previous_close": float(index_data.get("previous_close", 0)),
                "previous_1_week": float(index_data.get("previous_1_week", 0)),
                "previous_1_month": float(index_data.get("previous_1_month", 0)),
                "timestamp": index_data.get("timestamp", datetime.now().isoformat())
            }
        else:
            raise RuntimeError(f"Fear & Greed API error: {response.status_code} - {response.text}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Fear & Greed data: {str(e)}")

def get_fear_greed_components():
    """
    Fetch all component scores and changes for the CNN Fear & Greed Index.
    Returns a dict with all components, scores, and changes.
    """
    url = "https://cnn-fear-and-greed-index.p.rapidapi.com/cnn/v1/fear_and_greed/components"
    headers = {
        "x-rapidapi-key": FEAR_GREED_API_KEY,
        "x-rapidapi-host": "cnn-fear-and-greed-index.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            components = data.get("components", [])
            # Each component: {"label":..., "score":..., "previous_close":..., "one_week_ago":..., ...}
            return components
        else:
            raise RuntimeError(f"Fear & Greed Components API error: {response.status_code} - {response.text}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Fear & Greed components: {str(e)}")

# --- Visualization ---
def plot_fear_greed_components(components, output_path=os.path.join(OUTPUT_DIR, "fear_components.png")):
    """
    Plot a 3x3 grid of component scores and changes.
    """
    plt.figure(figsize=(12, 10))
    for i, comp in enumerate(components):
        plt.subplot(3, 3, i+1)
        labels = ["Current", "Prev Close", "1W Ago", "1M Ago"]
        values = [comp.get("score"), comp.get("previous_close"), comp.get("one_week_ago"), comp.get("one_month_ago")]
        plt.bar(labels, values, color="#8e44ad")
        plt.title(comp.get("label", ""), fontsize=10)
        plt.ylim(0, 100)
        for j, v in enumerate(values):
            plt.text(j, v+2, str(v), ha='center', fontsize=8)
        plt.xticks(rotation=15)
    plt.tight_layout()
    plt.suptitle("CNN Fear & Greed Index Components", fontsize=16, y=1.02)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"✅ Component chart saved to {output_path}")

def plot_fear_greed_index(index_data, output_path=os.path.join(OUTPUT_DIR, "fear_greed_index.png")):
    """
    Plot the main Fear & Greed Index with historical data.
    """
    plt.figure(figsize=(12, 8))
    
    # Create subplot for main index
    plt.subplot(2, 1, 1)
    labels = ["Current", "Prev Close", "1W Ago", "1M Ago"]
    values = [
        index_data["score"],
        index_data["previous_close"],
        index_data["previous_1_week"],
        index_data["previous_1_month"]
    ]
    
    # Color based on rating
    colors = []
    for val in values:
        if val >= 80:
            colors.append("#e74c3c")  # Extreme Greed (Red)
        elif val >= 60:
            colors.append("#f39c12")  # Greed (Orange)
        elif val >= 40:
            colors.append("#f1c40f")  # Neutral (Yellow)
        elif val >= 20:
            colors.append("#3498db")  # Fear (Blue)
        else:
            colors.append("#2c3e50")  # Extreme Fear (Dark Blue)
    
    bars = plt.bar(labels, values, color=colors)
    plt.title(f"CNN Fear & Greed Index: {index_data['score']} ({index_data['rating']})", fontsize=14, fontweight='bold')
    plt.ylabel("Score")
    plt.ylim(0, 100)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                f"{value:.1f}", ha='center', va='bottom', fontweight='bold')
    
    # Add rating zones
    plt.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Extreme Greed')
    plt.axhline(y=60, color='orange', linestyle='--', alpha=0.7, label='Greed')
    plt.axhline(y=40, color='yellow', linestyle='--', alpha=0.7, label='Neutral')
    plt.axhline(y=20, color='blue', linestyle='--', alpha=0.7, label='Fear')
    plt.axhline(y=0, color='darkblue', linestyle='--', alpha=0.7, label='Extreme Fear')
    
    plt.legend(loc='upper right')
    plt.grid(True, alpha=0.3)
    
    # Add timestamp
    plt.subplot(2, 1, 2)
    plt.text(0.5, 0.5, f"Last Updated: {index_data['timestamp']}", 
             ha='center', va='center', fontsize=12, style='italic')
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✅ Fear & Greed Index chart saved to {output_path}")

# --- Markdown/HTML Table ---
def summarize_fear_greed(components, output_path=os.path.join(OUTPUT_DIR, "fear_components.md"), html=False):
    """
    Create a Markdown or HTML table report of all components.
    """
    if not isinstance(components, list) or not components or not all(isinstance(x, dict) for x in components):
        print("⚠️  No components data available or invalid format.")
        return ""
    df = pd.DataFrame(components)
    if not hasattr(df, 'columns') or df.empty or not isinstance(df.columns, pd.Index):
        print("⚠️  No valid columns found in components data")
        return ""
    required_columns = ["label", "score", "previous_close", "one_week_ago", "one_month_ago"]
    available_columns = df.columns.tolist()
    columns_to_use = [col for col in required_columns if col in available_columns]
    if not columns_to_use:
        print("⚠️  No valid columns found in components data")
        return ""
    df = df[columns_to_use]
    column_mapping = {
        "label": "Component",
        "score": "Current", 
        "previous_close": "Prev Close",
        "one_week_ago": "1W Ago",
        "one_month_ago": "1M Ago"
    }
    df.columns = [column_mapping.get(col, col) for col in columns_to_use]
    if html:
        table = df.to_html(index=False, border=0)
        with open(output_path.replace('.md', '.html'), 'w', encoding='utf-8') as f:
            f.write(table)
        print(f"✅ HTML report saved to {output_path.replace('.md', '.html')}")
    else:
        table = df.to_markdown(index=False)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(table)
        print(f"✅ Markdown report saved to {output_path}")
    return table

def summarize_fear_greed_index(index_data, output_path=os.path.join(OUTPUT_DIR, "fear_greed_index.md"), html=False):
    """
    Create a Markdown or HTML report of the main Fear & Greed Index.
    """
    data = {
        "Metric": ["Current Score", "Rating", "Previous Close", "1 Week Ago", "1 Month Ago", "Last Updated"],
        "Value": [
            f"{index_data['score']:.1f}",
            index_data['rating'],
            f"{index_data['previous_close']:.1f}",
            f"{index_data['previous_1_week']:.1f}",
            f"{index_data['previous_1_month']:.1f}",
            index_data['timestamp']
        ]
    }
    
    df = pd.DataFrame(data)
    
    if html:
        table = df.to_html(index=False, border=0)
        with open(output_path.replace('.md', '.html'), 'w', encoding='utf-8') as f:
            f.write(table)
        print(f"✅ HTML report saved to {output_path.replace('.md', '.html')}")
    else:
        table = df.to_markdown(index=False)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(table)
        print(f"✅ Markdown report saved to {output_path}")
    return table

# --- CLI ---
def main():
    parser = argparse.ArgumentParser(description="CNN Fear & Greed Dashboard")
    parser.add_argument('--chart', action='store_true', help='Generate and save the component chart PNG')
    parser.add_argument('--index-chart', action='store_true', help='Generate and save the main index chart PNG')
    parser.add_argument('--report', action='store_true', help='Generate and save the Markdown/HTML report')
    parser.add_argument('--index-report', action='store_true', help='Generate and save the main index report')
    parser.add_argument('--html', action='store_true', help='Output HTML instead of Markdown for the report')
    parser.add_argument('--components', action='store_true', help='Fetch and display component data')
    parser.add_argument('--index', action='store_true', help='Fetch and display main index data')
    args = parser.parse_args()

    try:
        if args.components or args.chart or args.report:
            components = get_fear_greed_components()
            if args.components:
                print("📊 Fear & Greed Components:")
                for comp in components:
                    print(f"  {comp.get('label', 'Unknown')}: {comp.get('score', 0)}")
            if args.chart:
                plot_fear_greed_components(components)
            if args.report:
                summarize_fear_greed(components, html=args.html)
        
        if args.index or args.index_chart or args.index_report:
            index_data = get_fear_greed_report()
            if args.index:
                print("📊 Fear & Greed Index:")
                print(f"  Score: {index_data['score']:.1f}")
                print(f"  Rating: {index_data['rating']}")
                print(f"  Previous Close: {index_data['previous_close']:.1f}")
                print(f"  1 Week Ago: {index_data['previous_1_week']:.1f}")
                print(f"  1 Month Ago: {index_data['previous_1_month']:.1f}")
                print(f"  Timestamp: {index_data['timestamp']}")
            if args.index_chart:
                plot_fear_greed_index(index_data)
            if args.index_report:
                summarize_fear_greed_index(index_data, html=args.html)
        
        if not any([args.chart, args.index_chart, args.report, args.index_report, args.components, args.index]):
            print("No action specified. Use --chart, --index-chart, --report, --index-report, --components, or --index.")
            
    except Exception as e:
        print(f"❌ Failed to fetch Fear & Greed data: {e}")

if __name__ == "__main__":
    main() 