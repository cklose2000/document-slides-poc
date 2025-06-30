"""
Chart Generator for PowerPoint Presentations

This module creates professional charts for PowerPoint slides using
matplotlib and integrates with the brand template system for
consistent styling.
"""

import io
import base64
from typing import Dict, List, Any, Optional, Tuple, Union
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Rectangle
import numpy as np
from PIL import Image
from io import BytesIO

# Configure matplotlib for better rendering
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'


class ChartGenerator:
    """Generate branded charts for PowerPoint presentations"""
    
    def __init__(self, brand_config: Optional[Dict[str, Any]] = None):
        """Initialize with brand configuration"""
        self.brand_config = brand_config or self._get_default_brand_config()
        self._setup_chart_style()
    
    def _get_default_brand_config(self) -> Dict[str, Any]:
        """Get default brand configuration if none provided"""
        return {
            'colors': {
                'primary': '#1f77b4',  # Professional blue
                'secondary': '#ff7f0e',  # Complementary orange
                'accent1': '#2ca02c',  # Green for positive
                'accent2': '#d62728',  # Red for negative
                'background': '#FFFFFF',
                'text': '#333333'  # Softer than pure black
            },
            'fonts': {
                'title_font': 'DejaVu Sans',
                'body_font': 'DejaVu Sans', 
                'title_size': 16,
                'body_size': 12
            }
        }
    
    def _setup_chart_style(self):
        """Setup matplotlib style based on brand configuration"""
        colors = self.brand_config.get('colors', {})
        fonts = self.brand_config.get('fonts', {})
        
        # Set default color cycle
        color_cycle = [
            colors.get('primary', '#4F81BD'),
            colors.get('secondary', '#F79646'),
            colors.get('accent1', '#9BBB59'),
            colors.get('accent2', '#8064A2'),
            '#4BACC6',
            '#C0504D',
            '#3F3F3F'
        ]
        plt.rcParams['axes.prop_cycle'] = plt.cycler('color', color_cycle)
        
        # Set font properties
        plt.rcParams['font.family'] = fonts.get('body_font', 'Arial')
        plt.rcParams['font.size'] = fonts.get('body_size', 12)
        plt.rcParams['axes.titlesize'] = fonts.get('title_size', 16)
        plt.rcParams['axes.labelsize'] = fonts.get('body_size', 12)
        
        # Set text color
        text_color = colors.get('text', '#000000')
        plt.rcParams['text.color'] = text_color
        plt.rcParams['axes.labelcolor'] = text_color
        plt.rcParams['xtick.color'] = text_color
        plt.rcParams['ytick.color'] = text_color
    
    def create_bar_chart(self, data: Dict[str, Union[int, float]], 
                        title: str = "", 
                        x_label: str = "",
                        y_label: str = "",
                        orientation: str = "vertical",
                        size: Tuple[float, float] = (8, 6),
                        add_value_labels: bool = True,
                        add_gridlines: bool = True,
                        gradient_fill: bool = True) -> BytesIO:
        """
        Create a bar chart with brand styling and enhanced visuals
        
        Args:
            data: Dictionary of labels to values
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            orientation: 'vertical' or 'horizontal'
            size: Figure size in inches
            add_value_labels: Add value labels on bars
            add_gridlines: Add subtle gridlines
            gradient_fill: Use gradient fills (simulated with transparency)
            
        Returns:
            BytesIO object containing the chart image
        """
        fig, ax = plt.subplots(figsize=size, facecolor='white')
        
        labels = list(data.keys())
        values = list(data.values())
        
        # Create bars with brand colors
        colors = self._get_chart_colors(len(labels))
        
        if orientation == 'horizontal':
            # Sort values for better visual hierarchy
            sorted_data = sorted(zip(labels, values, colors), key=lambda x: x[1])
            labels, values, colors = zip(*sorted_data)
            
            bars = ax.barh(labels, values, color=colors, alpha=0.85 if gradient_fill else 1.0)
            ax.set_xlabel(y_label if y_label else "Value ($)")
            ax.set_ylabel(x_label)
            
            # Add subtle gridlines
            if add_gridlines:
                ax.grid(axis='x', alpha=0.2, linestyle='--', linewidth=0.5)
                ax.set_axisbelow(True)
        else:
            bars = ax.bar(labels, values, color=colors, alpha=0.85 if gradient_fill else 1.0)
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label if y_label else "Value ($)")
            
            # Rotate x labels if needed
            if len(labels) > 5:
                plt.xticks(rotation=45, ha='right')
            
            # Add subtle gridlines
            if add_gridlines:
                ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.5)
                ax.set_axisbelow(True)
        
        # Add modern gradient effect with enhanced styling
        if gradient_fill:
            for bar, color in zip(bars, colors):
                # Create darker edge color for depth
                edge_color = self._darken_color(color, factor=0.3)
                bar.set_edgecolor(edge_color)
                bar.set_linewidth(3)
                
                # Add subtle shadow effect
                if hasattr(bar, 'set_path_effects'):
                    from matplotlib.patches import Shadow
                    bar.set_path_effects([Shadow(offset=(2, -2), alpha=0.1)])
        
        # Add value labels on bars
        if add_value_labels:
            self._add_bar_labels_enhanced(ax, bars, orientation, values)
        
        # Set title with subtitle for time period
        if title:
            ax.set_title(title, fontsize=self.brand_config['fonts']['title_size'], 
                        pad=20, fontweight='bold')
        
        # Style the plot with enhanced aesthetics
        self._style_chart_enhanced(ax)
        
        # Save to BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    def create_line_chart(self, data: Dict[str, List[Union[int, float]]], 
                         title: str = "",
                         x_label: str = "",
                         y_label: str = "",
                         x_values: Optional[List] = None,
                         size: Tuple[float, float] = (8, 6)) -> BytesIO:
        """
        Create a line chart with brand styling
        
        Args:
            data: Dictionary of series names to values
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            x_values: X-axis values (optional)
            size: Figure size in inches
            
        Returns:
            BytesIO object containing the chart image
        """
        fig, ax = plt.subplots(figsize=size, facecolor='white')
        
        colors = self._get_chart_colors(len(data))
        
        for i, (series_name, values) in enumerate(data.items()):
            if x_values is None:
                x_values = list(range(len(values)))
            
            ax.plot(x_values, values, label=series_name, color=colors[i], 
                   linewidth=2.5, marker='o', markersize=6)
        
        # Set labels
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        
        # Set title
        if title:
            ax.set_title(title, fontsize=self.brand_config['fonts']['title_size'], 
                        pad=20, fontweight='bold')
        
        # Add legend
        if len(data) > 1:
            ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        
        # Style the plot
        self._style_chart(ax)
        
        # Save to BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    def create_pie_chart(self, data: Dict[str, Union[int, float]], 
                        title: str = "",
                        show_percentages: bool = True,
                        explode_largest: bool = False,
                        size: Tuple[float, float] = (8, 8)) -> BytesIO:
        """
        Create a pie chart with brand styling
        
        Args:
            data: Dictionary of labels to values
            title: Chart title
            show_percentages: Show percentage labels
            explode_largest: Explode the largest slice
            size: Figure size in inches
            
        Returns:
            BytesIO object containing the chart image
        """
        fig, ax = plt.subplots(figsize=size, facecolor='white')
        
        labels = list(data.keys())
        values = list(data.values())
        colors = self._get_chart_colors(len(labels))
        
        # Explode largest slice if requested
        explode = [0] * len(values)
        if explode_largest and values:
            max_idx = values.index(max(values))
            explode[max_idx] = 0.1
        
        # Create pie chart
        if show_percentages:
            autopct = '%1.1f%%'
        else:
            autopct = None
        
        wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors,
                                          autopct=autopct, explode=explode,
                                          startangle=90, shadow=True)
        
        # Style text
        for text in texts:
            text.set_fontsize(self.brand_config['fonts']['body_size'])
        
        if show_percentages:
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(self.brand_config['fonts']['body_size'] - 2)
        
        # Set title
        if title:
            ax.set_title(title, fontsize=self.brand_config['fonts']['title_size'], 
                        pad=20, fontweight='bold')
        
        # Equal aspect ratio ensures circular pie
        ax.axis('equal')
        
        # Save to BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    def create_waterfall_chart(self, data: List[Tuple[str, float]], 
                              title: str = "",
                              y_label: str = "Value",
                              size: Tuple[float, float] = (10, 6)) -> BytesIO:
        """
        Create a waterfall chart for financial data
        
        Args:
            data: List of tuples (label, value)
            title: Chart title
            y_label: Y-axis label
            size: Figure size in inches
            
        Returns:
            BytesIO object containing the chart image
        """
        fig, ax = plt.subplots(figsize=size, facecolor='white')
        
        # Calculate cumulative values
        cumulative = 0
        step_values = []
        colors = []
        
        for i, (label, value) in enumerate(data):
            if i == 0:  # Starting value
                step_values.append((0, value))
                colors.append(self.brand_config['colors']['primary'])
            else:
                step_values.append((cumulative, value))
                if value >= 0:
                    colors.append(self.brand_config['colors']['accent1'])  # Positive
                else:
                    colors.append(self.brand_config['colors']['secondary'])  # Negative
            cumulative += value
        
        # Add final total
        labels = [item[0] for item in data] + ['Total']
        step_values.append((0, cumulative))
        colors.append(self.brand_config['colors']['primary'])
        
        # Create bars
        x_pos = range(len(labels))
        
        for i, ((bottom, height), color) in enumerate(zip(step_values, colors)):
            ax.bar(i, abs(height), bottom=bottom if height >= 0 else bottom + height,
                  color=color, edgecolor='black', linewidth=1)
        
        # Add connecting lines
        for i in range(len(step_values) - 2):
            if i == 0:
                y1 = step_values[i][1]
            else:
                y1 = step_values[i][0] + step_values[i][1]
            y2 = step_values[i + 1][0]
            
            ax.plot([i + 0.4, i + 1.4], [y1, y2], 'k--', alpha=0.5)
        
        # Set labels
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=45 if len(labels) > 5 else 0, ha='right')
        ax.set_ylabel(y_label)
        
        # Set title
        if title:
            ax.set_title(title, fontsize=self.brand_config['fonts']['title_size'], 
                        pad=20, fontweight='bold')
        
        # Style the plot
        self._style_chart(ax)
        
        # Save to BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    def create_scatter_plot(self, x_data: List[float], y_data: List[float],
                           labels: Optional[List[str]] = None,
                           title: str = "",
                           x_label: str = "",
                           y_label: str = "",
                           trendline: bool = True,
                           size: Tuple[float, float] = (8, 6)) -> BytesIO:
        """
        Create a scatter plot with optional trendline
        
        Args:
            x_data: X-axis values
            y_data: Y-axis values
            labels: Point labels (optional)
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            trendline: Add trendline
            size: Figure size in inches
            
        Returns:
            BytesIO object containing the chart image
        """
        fig, ax = plt.subplots(figsize=size, facecolor='white')
        
        # Create scatter plot
        scatter = ax.scatter(x_data, y_data, 
                           c=self.brand_config['colors']['primary'],
                           s=100, alpha=0.7, edgecolors='black', linewidth=1)
        
        # Add labels if provided
        if labels:
            for i, label in enumerate(labels):
                ax.annotate(label, (x_data[i], y_data[i]), 
                          xytext=(5, 5), textcoords='offset points',
                          fontsize=8, alpha=0.7)
        
        # Add trendline if requested
        if trendline and len(x_data) > 1:
            z = np.polyfit(x_data, y_data, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(min(x_data), max(x_data), 100)
            ax.plot(x_trend, p(x_trend), "--", 
                   color=self.brand_config['colors']['secondary'],
                   linewidth=2, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
            ax.legend()
        
        # Set labels
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        
        # Set title
        if title:
            ax.set_title(title, fontsize=self.brand_config['fonts']['title_size'], 
                        pad=20, fontweight='bold')
        
        # Style the plot
        self._style_chart(ax)
        
        # Save to BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    def _get_chart_colors(self, n: int) -> List[str]:
        """Get n colors from the brand palette"""
        colors = self.brand_config.get('colors', {})
        
        color_list = [
            colors.get('primary', '#4F81BD'),
            colors.get('secondary', '#F79646'),
            colors.get('accent1', '#9BBB59'),
            colors.get('accent2', '#8064A2'),
            '#4BACC6',
            '#C0504D',
            '#3F3F3F'
        ]
        
        # Repeat colors if needed
        while len(color_list) < n:
            color_list.extend(color_list)
        
        return color_list[:n]
    
    def _add_bar_labels_enhanced(self, ax, bars, orientation: str, values):
        """Add enhanced value labels to bars with better formatting"""
        for bar, value in zip(bars, values):
            if orientation == 'horizontal':
                width = bar.get_width()
                label_x = width
                label_y = bar.get_y() + bar.get_height() / 2
                ha = 'left' if width >= 0 else 'right'
                va = 'center'
                offset = max(width * 0.02, 100000)  # Dynamic offset based on value
                
                # Format large numbers nicely
                if abs(value) >= 1_000_000:
                    label_text = f'${value/1_000_000:.1f}M'
                elif abs(value) >= 1_000:
                    label_text = f'${value/1_000:.0f}K'
                else:
                    label_text = f'${value:,.0f}'
                
                ax.text(label_x + offset, label_y, label_text,
                       ha=ha, va=va, fontsize=10, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                               edgecolor='none', alpha=0.7))
            else:
                height = bar.get_height()
                label_x = bar.get_x() + bar.get_width() / 2
                label_y = height
                ha = 'center'
                va = 'bottom' if height >= 0 else 'top'
                offset = height * 0.02 if height >= 0 else -height * 0.02
                
                # Format large numbers nicely
                if abs(value) >= 1_000_000:
                    label_text = f'${value/1_000_000:.1f}M'
                elif abs(value) >= 1_000:
                    label_text = f'${value/1_000:.0f}K'
                else:
                    label_text = f'${value:,.0f}'
                
                ax.text(label_x, label_y + offset, label_text,
                       ha=ha, va=va, fontsize=10, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                               edgecolor='none', alpha=0.7))
    
    def _add_bar_labels(self, ax, bars, orientation: str):
        """Add value labels to bars (legacy method for compatibility)"""
        for bar in bars:
            if orientation == 'horizontal':
                width = bar.get_width()
                label_x = width
                label_y = bar.get_y() + bar.get_height() / 2
                ha = 'left' if width >= 0 else 'right'
                va = 'center'
                offset = width * 0.01 if width >= 0 else -width * 0.01  # Proportional offset
                
                # Format large numbers nicely
                if abs(width) >= 1_000_000:
                    label_text = f'${width/1_000_000:.1f}M'
                elif abs(width) >= 1_000:
                    label_text = f'${width/1_000:.0f}K'
                else:
                    label_text = f'${width:,.0f}'
                
                ax.text(label_x + offset, label_y, label_text,
                       ha=ha, va=va, fontsize=9, fontweight='bold')
            else:
                height = bar.get_height()
                label_x = bar.get_x() + bar.get_width() / 2
                label_y = height
                ha = 'center'
                va = 'bottom' if height >= 0 else 'top'
                offset = 3 if height >= 0 else -3
                
                # Format large numbers nicely
                if abs(height) >= 1_000_000:
                    label_text = f'${height/1_000_000:.1f}M'
                elif abs(height) >= 1_000:
                    label_text = f'${height/1_000:.0f}K'
                else:
                    label_text = f'${height:,.0f}'
                
                ax.text(label_x, label_y + offset, label_text,
                       ha=ha, va=va, fontsize=9, fontweight='bold')
    
    def _style_chart(self, ax):
        """Apply consistent styling to charts"""
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Make remaining spines lighter
        ax.spines['bottom'].set_color('#CCCCCC')
        ax.spines['left'].set_color('#CCCCCC')
        
        # Lighten grid
        ax.grid(True, alpha=0.3)
        
        # Set tick parameters
        ax.tick_params(colors='#666666', which='both')
    
    def _style_chart_enhanced(self, ax):
        """Apply enhanced styling to charts with better aesthetics"""
        # Remove all spines for cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(0.5)
        ax.spines['left'].set_linewidth(0.5)
        ax.spines['bottom'].set_color('#CCCCCC')
        ax.spines['left'].set_color('#CCCCCC')
        
        # Set tick parameters
        ax.tick_params(colors='#666666', which='both', length=5, width=0.5)
        
        # Format y-axis for currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000000:.1f}M' if x >= 1000000 else f'${x/1000:.0f}K' if x >= 1000 else f'${x:.0f}'))
        
        # Add subtle background
        ax.set_facecolor('#FAFAFA')
    
    def _darken_color(self, color: str, factor: float = 0.3) -> str:
        """Darken a hex color by the specified factor for depth effects"""
        # Remove # if present
        color = color.lstrip('#')
        
        # Convert to RGB
        try:
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            
            # Darken each component
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color  # Return original if conversion fails
    
    def save_chart_to_file(self, chart_buffer: BytesIO, filepath: str):
        """Save chart buffer to file"""
        with open(filepath, 'wb') as f:
            f.write(chart_buffer.getvalue())
    
    def get_chart_as_base64(self, chart_buffer: BytesIO) -> str:
        """Convert chart buffer to base64 string"""
        return base64.b64encode(chart_buffer.getvalue()).decode('utf-8')


# Example usage
if __name__ == "__main__":
    # Create chart generator with brand config
    brand_config = {
        'colors': {
            'primary': '#003366',
            'secondary': '#FF6600',
            'accent1': '#0066CC',
            'accent2': '#666666'
        },
        'fonts': {
            'title_font': 'Arial',
            'body_font': 'Arial',
            'title_size': 18,
            'body_size': 12
        }
    }
    
    chart_gen = ChartGenerator(brand_config)
    
    # Example bar chart
    data = {
        'Q1 2024': 125000,
        'Q2 2024': 145000,
        'Q3 2024': 162000,
        'Q4 2024': 189000
    }
    
    chart_buffer = chart_gen.create_bar_chart(
        data,
        title="Quarterly Revenue Growth",
        x_label="Quarter",
        y_label="Revenue ($)"
    )
    
    # Save to file
    chart_gen.save_chart_to_file(chart_buffer, "revenue_chart.png")