"""
Decision Tree Visualization for MLAlgorithm.decision_tree_algorithm()
This script creates a visual representation of the decision tree logic used to determine BUY/SELL/HOLD signals
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

def create_decision_tree_visualization():
    """
    Creates a comprehensive visual representation of the decision tree algorithm
    """
    fig, ax = plt.subplots(1, 1, figsize=(20, 14))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Color scheme
    color_start = '#E8F4F8'
    color_check = '#FFF4E6'
    color_buy = '#D4EDDA'
    color_sell = '#F8D7DA'
    color_hold = '#E2E3E5'
    color_decision = '#D1ECF1'
    
    def draw_box(ax, x, y, width, height, text, color, fontsize=9, fontweight='normal'):
        """Helper function to draw a box with text"""
        box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                            boxstyle="round,pad=0.1", 
                            edgecolor='black', facecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=fontsize, 
                fontweight=fontweight, wrap=True)
    
    def draw_arrow(ax, x1, y1, x2, y2, label=''):
        """Helper function to draw an arrow"""
        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                              arrowstyle='->', mutation_scale=20, 
                              linewidth=2, color='black')
        ax.add_patch(arrow)
        if label:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mid_x + 2, mid_y, label, fontsize=8, style='italic')
    
    # Title
    ax.text(50, 97, 'Decision Tree Algorithm Flow', ha='center', fontsize=16, fontweight='bold')
    
    # Level 1: Start - Input Validation
    draw_box(ax, 50, 90, 12, 4, 'START\nInput: ticker, momentum_rate,\ndesired_change, user_id', color_start, 9, 'bold')
    draw_arrow(ax, 50, 88, 50, 84)
    
    # Level 2: Fetch Data
    draw_box(ax, 50, 81, 14, 5, 'Fetch Data:\n• Predicted Price (ML model)\n• User Buy Price (if portfolio)\n• Current Market Price', color_check, 9)
    draw_arrow(ax, 50, 78.5, 50, 75)
    
    # Level 3: Check Predicted Price
    draw_box(ax, 50, 72, 14, 4, 'Check: Predicted Price\nValid?', color_decision, 9, 'bold')
    draw_arrow(ax, 42, 70, 25, 65, 'NO')
    draw_box(ax, 20, 62, 8, 3, 'HOLD\n(no_prediction)', color_hold, 9, 'bold')
    draw_arrow(ax, 50, 70, 50, 66, 'YES')
    
    # Level 4: Gather Feature Data
    draw_box(ax, 50, 63, 16, 5, 'Gather Features:\n• Sentiment Score\n• Market Cap/Revenue Ratio\n• Trading Volume', color_check, 9)
    draw_arrow(ax, 50, 60.5, 50, 57)
    
    # Level 5: Calculate Percentages
    draw_box(ax, 50, 54, 14, 4, 'Calculate % Changes:\n• Predicted vs Buy Price\n• Predicted vs Current Price', color_check, 9)
    draw_arrow(ax, 50, 52, 50, 49)
    
    # Level 6: Start Scoring Decision Tree
    draw_box(ax, 50, 46, 12, 4, 'Initialize Scoring:\nbuy_score = 0\nsell_score = 0', color_decision, 9, 'bold')
    
    # LEFT SIDE: SELL SIGNALS
    draw_arrow(ax, 35, 44, 25, 39, 'Sell Checks')
    draw_box(ax, 20, 36, 10, 3, 'Own Stock?', color_decision, 8, 'bold')
    draw_arrow(ax, 15, 34.5, 10, 31, 'YES')
    draw_box(ax, 8, 28, 8, 4, 'Take Profit?\npredicted_pct_vs_buy\n≥ desired_change\n→ +6 points', color_sell, 7)
    
    draw_arrow(ax, 20, 34.5, 25, 31, 'YES')
    draw_box(ax, 28, 28, 8, 4, 'Stop Loss?\npredicted_pct_vs_buy\n≤ -5%\n→ +5 points', color_sell, 7)
    
    # RIGHT SIDE: BUY SIGNALS
    draw_arrow(ax, 65, 44, 75, 39, 'Buy Checks')
    
    # Buy Signal 1: Upside
    draw_box(ax, 75, 36, 10, 3, 'Price Upside?', color_decision, 8, 'bold')
    draw_arrow(ax, 75, 34.5, 75, 31)
    draw_box(ax, 75, 28, 10, 5, 'Strong Upside?\npredicted_pct_vs_now\n≥ 8%\n→ +5 points\n(or ≥4% → +2)', color_buy, 7)
    
    # Sentiment Signals
    draw_arrow(ax, 50, 44, 50, 39)
    draw_box(ax, 50, 36, 10, 3, 'Sentiment Score', color_decision, 8, 'bold')
    draw_arrow(ax, 50, 34.5, 50, 31)
    draw_box(ax, 50, 26, 12, 6, 'Very Positive ≥0.35?\n→ +3 BUY\nWeak Pos ≥0.15?\n→ +1 BUY\nNegative ≤-0.35?\n→ +3 SELL', color_check, 7)
    
    # Market Cap Ratio
    draw_arrow(ax, 50, 44, 35, 39)
    draw_box(ax, 32, 36, 10, 3, 'Market Cap/\nRevenue Ratio', color_decision, 8, 'bold')
    draw_arrow(ax, 32, 34.5, 32, 31)
    draw_box(ax, 32, 24, 12, 7, '<50 → +2 BUY\n50-200 → +1 BUY\n200-500 → 0 HOLD\n500-1000 → +2 SELL\n>1000 → +5 SELL', color_check, 7)
    
    # Momentum
    draw_arrow(ax, 50, 44, 65, 39)
    draw_box(ax, 68, 36, 10, 3, 'Momentum Rate', color_decision, 8, 'bold')
    draw_arrow(ax, 68, 34.5, 68, 31)
    draw_box(ax, 68, 28, 10, 4, '>0.5% → +1 BUY\n<-0.5% → +1 SELL\nVolume <1000\n→ -1 penalty', color_check, 7)
    
    # Bottom: Final Decision Logic
    draw_arrow(ax, 50, 18, 50, 15)
    draw_box(ax, 50, 12, 14, 4, 'Final Decision (MARGIN=3):\nIF sell_score - buy_score ≥ 3: SELL/AVOID\nIF buy_score - sell_score ≥ 3: BUY\nELSE: HOLD', color_decision, 9, 'bold')
    
    draw_arrow(ax, 50, 10, 50, 7)
    draw_box(ax, 50, 4, 12, 3, 'RETURN: Action + Details Dict\n(contains all scores and reasoning)', color_start, 9, 'bold')
    
    # Add legend
    legend_y = 98
    legend_items = [
        (color_start, 'Input/Output'),
        (color_check, 'Data Fetch/Process'),
        (color_decision, 'Decision Point'),
        (color_buy, 'Buy Signal'),
        (color_sell, 'Sell Signal'),
        (color_hold, 'Hold Signal')
    ]
    
    for i, (color, label) in enumerate(legend_items):
        x = 2 + (i % 3) * 18
        y = legend_y - (i // 3) * 3
        patch = mpatches.Patch(facecolor=color, edgecolor='black', linewidth=1)
        ax.legend(handles=[patch], labels=[label], loc='upper left', 
                 bbox_to_anchor=(x/100, (y+1)/100), fontsize=8)
    
    plt.tight_layout()
    return fig

def create_scoring_system_chart():
    """
    Creates a detailed breakdown chart of the scoring system
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Decision Tree Scoring System Breakdown', fontsize=16, fontweight='bold')
    
    # 1. Price-based Signals
    ax = axes[0, 0]
    categories = ['Strong\nUpside\n(≥8%)', 'Moderate\nUpside\n(≥4%)', 'Take\nProfit', 'Stop\nLoss']
    points = [5, 2, 6, 5]
    colors_chart = ['#90EE90', '#90EE90', '#FFB6C6', '#FF6B6B']
    bars = ax.bar(categories, points, color=colors_chart, edgecolor='black', linewidth=2)
    ax.set_ylabel('Points', fontsize=11, fontweight='bold')
    ax.set_title('Price Movement Signals', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 7)
    for bar, point in zip(bars, points):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'+{point}', ha='center', va='bottom', fontweight='bold')
    
    # 2. Sentiment Analysis
    ax = axes[0, 1]
    sentiment_levels = ['Very Pos\n(≥0.35)', 'Weak Pos\n(≥0.15)', 'Weak Neg\n(≤-0.15)', 'Very Neg\n(≤-0.35)']
    sentiment_points = [3, 1, -1, -3]
    colors_sentiment = ['#28A745', '#90EE90', '#FFB6C6', '#DC3545']
    bars = ax.bar(sentiment_levels, sentiment_points, color=colors_sentiment, edgecolor='black', linewidth=2)
    ax.set_ylabel('Points', fontsize=11, fontweight='bold')
    ax.set_title('Sentiment Score Impact', fontsize=12, fontweight='bold')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_ylim(-4, 4)
    for bar, point in zip(bars, sentiment_points):
        height = bar.get_height()
        va = 'bottom' if point >= 0 else 'top'
        y_pos = height + 0.1 if point >= 0 else height - 0.1
        ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                f'{point:+d}', ha='center', va=va, fontweight='bold')
    
    # 3. Market Cap to Revenue Ratio
    ax = axes[0, 2]
    ratio_ranges = ['<50', '50-200', '200-500', '500-1k', '>1k']
    ratio_points = [2, 1, 0, -2, -5]
    colors_ratio = ['#28A745', '#90EE90', '#E2E3E5', '#FFB6C6', '#DC3545']
    bars = ax.bar(ratio_ranges, ratio_points, color=colors_ratio, edgecolor='black', linewidth=2)
    ax.set_ylabel('Points', fontsize=11, fontweight='bold')
    ax.set_xlabel('Ratio Range', fontsize=11, fontweight='bold')
    ax.set_title('Market Cap/Revenue Ratio Impact', fontsize=12, fontweight='bold')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_ylim(-6, 3)
    for bar, point in zip(bars, ratio_points):
        height = bar.get_height()
        va = 'bottom' if point >= 0 else 'top'
        y_pos = height + 0.2 if point >= 0 else height - 0.2
        ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                f'{point:+d}', ha='center', va=va, fontweight='bold')
    
    # 4. Momentum Rate
    ax = axes[1, 0]
    momentum_ranges = ['> +0.5%', '< -0.5%', 'Low Volume\n(<1000)']
    momentum_points = [1, -1, -1]
    colors_momentum = ['#28A745', '#DC3545', '#FFB6C6']
    bars = ax.bar(momentum_ranges, momentum_points, color=colors_momentum, edgecolor='black', linewidth=2)
    ax.set_ylabel('Points', fontsize=11, fontweight='bold')
    ax.set_title('Momentum & Volume Impact', fontsize=12, fontweight='bold')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_ylim(-2, 2)
    for bar, point in zip(bars, momentum_points):
        height = bar.get_height()
        va = 'bottom' if point >= 0 else 'top'
        y_pos = height + 0.05 if point >= 0 else height - 0.05
        ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                f'{point:+d}', ha='center', va=va, fontweight='bold')
    
    # 5. Final Decision Rules
    ax = axes[1, 1]
    ax.axis('off')
    decision_text = """
    FINAL DECISION LOGIC
    (MARGIN = 3 points)
    
    ┌─────────────────────────────────┐
    │ IF sell_score - buy_score ≥ 3   │
    │    → SELL (if owns) or AVOID     │
    ├─────────────────────────────────┤
    │ IF buy_score - sell_score ≥ 3   │
    │    → BUY                          │
    ├─────────────────────────────────┤
    │ ELSE                              │
    │    → HOLD                         │
    └─────────────────────────────────┘
    
    Primary Reason: Highest absolute
    contribution point
    """
    ax.text(0.1, 0.5, decision_text, fontsize=10, verticalalignment='center',
            family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 6. Example Scenarios
    ax = axes[1, 2]
    ax.axis('off')
    scenarios_text = """
    EXAMPLE SCENARIOS
    
    Scenario 1: Strong Buy Signal
    • Buy: 5 (strong upside) + 3 (sentiment)
    • Sell: 0
    • Result: BUY ✓
    
    Scenario 2: Stop Loss Hit
    • Buy: 2 (moderate upside)
    • Sell: 5 (stop loss)
    • Result: SELL ✓
    
    Scenario 3: Mixed Signals
    • Buy: 3, Sell: 2
    • Difference: 1 < 3
    • Result: HOLD ✓
    """
    ax.text(0.05, 0.5, scenarios_text, fontsize=9, verticalalignment='center',
            family='monospace', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    plt.tight_layout()
    return fig

# Main execution
if __name__ == "__main__":
    # Create and save decision tree flow diagram
    print("Creating Decision Tree Flow Diagram...")
    fig1 = create_decision_tree_visualization()
    fig1.savefig('decision_tree_flow.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: decision_tree_flow.png")
    
    # Create and save scoring system breakdown
    print("Creating Scoring System Breakdown Chart...")
    fig2 = create_scoring_system_chart()
    fig2.savefig('decision_tree_scoring_system.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: decision_tree_scoring_system.png")
    
    print("\nVisualization complete! Generated files:")
    print("  1. decision_tree_flow.png - Complete decision flow")
    print("  2. decision_tree_scoring_system.png - Scoring breakdown")
    
    plt.show()
