"""
Chart Generation Module for Branded Presentations

This module provides functionality to generate professional charts
with brand-consistent styling for PowerPoint presentations.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple, Union
import seaborn as sns

# Set default style
plt.style.use('seaborn-v0_8-darkgrid')

class ChartGenerator:
    """Generate branded charts for presentations"""
    
    def __init__(self, brand_config: Optional[Dict[str, Any]] = None):
        """Initialize with brand configuration"""
        self.brand_config = brand_config or self._get_default_brand_config()
        self._setup_chart_style()
    
    def _get_default_brand_config(self) -> Dict[str, Any]:
        """Get default brand configuration"""
        return {
            'theme_colors': {
                'primary': '#003366',
                'secondary': '#0066CC', 
                'accent1': '#FF6600',
                'accent2': '#00AA44',
                'dark1': '#333333',
                'dark2': '#666666',
                'light1': '#F0F0F0',
                'light2': '#CCCCCC'
            },
            'fonts': {
                'heading': {'family': 'Arial', 'size_large': 16},
                'body': {'family': 'Arial', 'size_medium': 12}
            }
        }
    
    def _setup_chart_style(self):
        """Setup matplotlib style based on brand config"""
        # Extract colors
        colors = self.brand_config.get('theme_colors', {})
        self.primary_color = colors.get('primary', '#003366')
        self.secondary_color = colors.get('secondary', '#0066CC')
        self.accent_colors = [
            colors.get('accent1', '#FF6600'),
            colors.get('accent2', '#00AA44'),
            self.primary_color,
            self.secondary_color
        ]
        
        # Extract fonts
        fonts = self.brand_config.get('fonts', {})
        self.title_font = fonts.get('heading', {}).get('family', 'Arial')
        self.body_font = fonts.get('body', {}).get('family', 'Arial')
        self.title_size = fonts.get('heading', {}).get('size_large', 16)
        self.body_size = fonts.get('body', {}).get('size_medium', 12)
        
        # Set matplotlib RC params
        plt.rcParams.update({
            'font.family': self.body_font,
            'font.size': self.body_size,
            'axes.titlesize': self.title_size,
            'axes.labelsize': self.body_size,
            'xtick.labelsize': self.body_size - 2,
            'ytick.labelsize': self.body_size - 2,
            'legend.fontsize': self.body_size - 2,
            'figure.titlesize': self.title_size
        })
    
    def create_bar_chart(self, data: Dict[str, float], 
                        title: str = "",
                        x_label: str = "",
                        y_label: str = "",
                        orientation: str = 'vertical',
                        size: Tuple[int, int] = (10, 6)) -> BytesIO:
        """Create a branded bar chart"""
        fig, ax = plt.subplots(figsize=size)
        
        # Prepare data
        categories = list(data.keys())
        values = list(data.values())
        
        # Create bars
        if orientation == 'vertical':
            bars = ax.bar(categories, values, color=self.primary_color)
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            
            # Rotate x labels if many categories
            if len(categories) > 5:
                plt.xticks(rotation=45, ha='right')
        else:
            bars = ax.barh(categories, values, color=self.primary_color)
            ax.set_xlabel(y_label)
            ax.set_ylabel(x_label)
        
        # Add value labels on bars
        for bar in bars:
            if orientation == 'vertical':
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:,.0f}',
                       ha='center', va='bottom', fontsize=self.body_size-2)
            else:
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2.,
                       f'{width:,.0f}',
                       ha='left', va='center', fontsize=self.body_size-2)
        
        # Style the chart
        ax.set_title(title, fontsize=self.title_size, pad=20, fontfamily=self.title_font)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add subtle grid
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    def create_line_chart(self, data: Dict[str, List[float]],
                         title: str = "",
                         x_label: str = "",
                         y_label: str = "",
                         x_values: Optional[List[Any]] = None,
                         size: Tuple[int, int] = (10, 6)) -> BytesIO:
        """Create a branded line chart"""
        fig, ax = plt.subplots(figsize=size)
        
        # Plot each series
        for i, (series_name, values) in enumerate(data.items()):
            x_vals = x_values if x_values else list(range(len(values)))
            color = self.accent_colors[i % len(self.accent_colors)]
            ax.plot(x_vals, values, label=series_name, color=color, 
                   linewidth=2.5, marker='o', markersize=6)
        
        # Style the chart
        ax.set_title(title, fontsize=self.title_size, pad=20, fontfamily=self.title_font)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        
        # Add legend if multiple series
        if len(data) > 1:
            ax.legend(loc='best', framealpha=0.9)
        
        # Style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    def create_pie_chart(self, data: Dict[str, float],
                        title: str = "",
                        show_percentages: bool = True,
                        explode_largest: bool = False,
                        size: Tuple[int, int] = (8, 8)) -> BytesIO:
        """Create a branded pie chart"""
        fig, ax = plt.subplots(figsize=size)
        
        # Prepare data
        labels = list(data.keys())
        values = list(data.values())
        
        # Create color palette
        colors = self.accent_colors * (len(labels) // len(self.accent_colors) + 1)
        colors = colors[:len(labels)]
        
        # Explode the largest slice if requested
        explode = None
        if explode_largest and len(values) > 0:
            max_idx = values.index(max(values))
            explode = [0.1 if i == max_idx else 0 for i in range(len(values))]
        
        # Create pie chart
        if show_percentages:
            autopct = '%1.1f%%'
        else:
            autopct = None
        
        wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors,
                                          autopct=autopct, startangle=90,
                                          explode=explode)
        
        # Style the text
        for text in texts:
            text.set_fontsize(self.body_size)
        
        if autotexts:
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(self.body_size - 2)
                autotext.set_weight('bold')
        
        ax.set_title(title, fontsize=self.title_size, pad=20, fontfamily=self.title_font)
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    def create_waterfall_chart(self, data: List[Tuple[str, float]],
                              title: str = "",
                              size: Tuple[int, int] = (12, 6)) -> BytesIO:
        """Create a waterfall chart for financial data"""
        fig, ax = plt.subplots(figsize=size)
        
        # Calculate cumulative values
        categories = [item[0] for item in data]
        values = [item[1] for item in data]
        cumulative = np.cumsum([0] + values)
        
        # Create bars
        for i, (cat, val) in enumerate(data):
            if i == 0:
                # First bar starts from 0
                bar = ax.bar(cat, val, bottom=0,
                           color=self.primary_color if val >= 0 else self.accent_colors[0])
            else:
                # Subsequent bars start from previous cumulative
                bar = ax.bar(cat, val, bottom=cumulative[i-1],
                           color=self.accent_colors[1] if val >= 0 else self.accent_colors[0])
            
            # Add connecting lines
            if i < len(data) - 1:
                ax.plot([i, i+1], [cumulative[i], cumulative[i]], 
                       'k--', alpha=0.5, linewidth=1)
            
            # Add value labels
            y_pos = cumulative[i-1] + val/2 if i > 0 else val/2
            ax.text(i, y_pos, f'{val:+,.0f}', ha='center', va='center',
                   fontsize=self.body_size-2, fontweight='bold')
        
        # Add final total bar
        total_idx = len(categories)
        ax.bar(total_idx, cumulative[-1], bottom=0, 
               color=self.primary_color, alpha=0.7)
        ax.text(total_idx, cumulative[-1]/2, f'{cumulative[-1]:,.0f}',
               ha='center', va='center', fontsize=self.body_size, fontweight='bold')
        
        # Customize
        ax.set_xticks(list(range(len(categories))) + [total_idx])
        ax.set_xticklabels(categories + ['Total'], rotation=45, ha='right')
        ax.set_title(title, fontsize=self.title_size, pad=20, fontfamily=self.title_font)
        ax.set_ylabel('Value')
        
        # Style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, axis='y', alpha=0.3)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    def create_scatter_plot(self, x_data: List[float], y_data: List[float],
                           title: str = "",
                           x_label: str = "",
                           y_label: str = "",
                           trend_line: bool = True,
                           size: Tuple[int, int] = (10, 6)) -> BytesIO:
        """Create a branded scatter plot"""
        fig, ax = plt.subplots(figsize=size)
        
        # Create scatter plot
        ax.scatter(x_data, y_data, color=self.primary_color, 
                  s=100, alpha=0.6, edgecolors='white', linewidth=1.5)
        
        # Add trend line if requested
        if trend_line and len(x_data) > 1:
            z = np.polyfit(x_data, y_data, 1)
            p = np.poly1d(z)
            ax.plot(x_data, p(x_data), color=self.accent_colors[0], 
                   linewidth=2, linestyle='--', alpha=0.8)
        
        # Style
        ax.set_title(title, fontsize=self.title_size, pad=20, fontfamily=self.title_font)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        buffer.seek(0)
        return buffer
