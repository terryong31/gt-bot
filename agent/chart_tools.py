"""
Chart Tools - Generate charts and visualizations from data.
Uses matplotlib to create bar, line, pie charts for data analysis.
"""

import os
import io
import re
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

# Malaysia timezone
MYT = timezone(timedelta(hours=8))


def get_chart_tools() -> list:
    """
    Create chart generation tools.
    These tools don't require user credentials - they're pure computation.
    """
    
    @tool
    def generate_chart(
        chart_type: str,
        labels: List[str],
        values: List[float],
        title: str,
        x_label: str = "",
        y_label: str = "",
        comparison_values: Optional[List[float]] = None,
        comparison_label: str = "Comparison"
    ) -> str:
        """
        Generate a chart image and save it for sending to the user.
        
        Args:
            chart_type: Type of chart - "bar", "line", "pie", "hbar" (horizontal bar)
            labels: Labels for x-axis (bar/line) or segments (pie)
            values: Numeric values to plot
            title: Chart title
            x_label: Label for x-axis (optional)
            y_label: Label for y-axis (optional)  
            comparison_values: Second set of values for grouped bar comparison (optional)
            comparison_label: Label for comparison data series (optional)
        
        Returns:
            Path to the generated chart image file
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend for server
            import matplotlib.pyplot as plt
            
            # Create figure with professional styling
            plt.style.use('seaborn-v0_8-whitegrid')
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Color scheme - professional blues
            primary_color = '#2E86AB'
            secondary_color = '#A23B72'
            colors = ['#2E86AB', '#F18F01', '#C73E1D', '#3B1F2B', '#95C623', '#5D4E6D']
            
            chart_type = chart_type.lower().strip()
            
            if chart_type == "bar":
                if comparison_values:
                    # Grouped bar chart
                    x = range(len(labels))
                    width = 0.35
                    ax.bar([i - width/2 for i in x], values, width, label=y_label or 'Current', color=primary_color)
                    ax.bar([i + width/2 for i in x], comparison_values, width, label=comparison_label, color=secondary_color)
                    ax.set_xticks(x)
                    ax.set_xticklabels(labels, rotation=45, ha='right')
                    ax.legend()
                else:
                    ax.bar(labels, values, color=primary_color)
                    plt.xticks(rotation=45, ha='right')
                    
            elif chart_type == "hbar":
                ax.barh(labels, values, color=primary_color)
                
            elif chart_type == "line":
                ax.plot(labels, values, marker='o', linewidth=2, markersize=8, color=primary_color)
                if comparison_values:
                    ax.plot(labels, comparison_values, marker='s', linewidth=2, markersize=8, 
                           color=secondary_color, label=comparison_label)
                    ax.legend()
                plt.xticks(rotation=45, ha='right')
                
            elif chart_type == "pie":
                ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors[:len(values)],
                      startangle=90, explode=[0.02] * len(values))
                ax.axis('equal')
                
            else:
                return f"❌ Unknown chart type: {chart_type}. Use 'bar', 'line', 'pie', or 'hbar'."
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            if x_label and chart_type not in ['pie', 'hbar']:
                ax.set_xlabel(x_label)
            if y_label and chart_type != 'pie':
                ax.set_ylabel(y_label)
            
            plt.tight_layout()
            
            # Save to temp file
            chart_dir = "/app/data/charts"
            os.makedirs(chart_dir, exist_ok=True)
            
            import uuid
            timestamp = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"chart_{timestamp}_{unique_id}.png"
            filepath = os.path.join(chart_dir, filename)
            
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            return f"CHART_FILE:{filepath}"
            
        except ImportError:
            return "❌ matplotlib not installed. Please add matplotlib to requirements.txt"
        except Exception as e:
            return f"❌ Error generating chart: {str(e)}"
    
    @tool
    def analyze_data(
        values: List[float],
        labels: Optional[List[str]] = None,
        comparison_values: Optional[List[float]] = None,
        metric_name: str = "value"
    ) -> str:
        """
        Analyze numerical data and provide statistical insights.
        Use this to get summary statistics before or after showing a chart.
        
        Args:
            values: List of numeric values to analyze
            labels: Optional labels corresponding to values  
            comparison_values: Previous period values for comparison
            metric_name: Name of what's being measured (e.g., "sales", "revenue")
        
        Returns:
            Summary statistics and insights as text
        """
        try:
            if not values:
                return "❌ No data to analyze."
            
            total = sum(values)
            avg = total / len(values)
            max_val = max(values)
            min_val = min(values)
            
            insights = []
            insights.append(f"Total {metric_name}: ${total:,.2f}" if metric_name in ['sales', 'revenue', 'amount'] else f"Total: {total:,.2f}")
            insights.append(f"Average: ${avg:,.2f}" if metric_name in ['sales', 'revenue', 'amount'] else f"Average: {avg:,.2f}")
            
            # Find top performer
            if labels and len(labels) == len(values):
                max_idx = values.index(max_val)
                insights.append(f"Top: {labels[max_idx]} (${max_val:,.2f})" if metric_name in ['sales', 'revenue', 'amount'] else f"Top: {labels[max_idx]} ({max_val:,.2f})")
            
            # Comparison analysis
            if comparison_values and len(comparison_values) == len(values):
                prev_total = sum(comparison_values)
                if prev_total > 0:
                    change_pct = ((total - prev_total) / prev_total) * 100
                    direction = "up" if change_pct > 0 else "down"
                    insights.append(f"Change: {direction} {abs(change_pct):.1f}% from previous period")
            
            # Trend analysis (if enough data points)
            if len(values) >= 3:
                first_half = sum(values[:len(values)//2])
                second_half = sum(values[len(values)//2:])
                if second_half > first_half * 1.1:
                    insights.append("Trend: Upward momentum in recent period")
                elif second_half < first_half * 0.9:
                    insights.append("Trend: Declining in recent period")
                else:
                    insights.append("Trend: Relatively stable")
            
            return "\n".join(insights)
            
        except Exception as e:
            return f"❌ Error analyzing data: {str(e)}"
    
    return [generate_chart, analyze_data]
