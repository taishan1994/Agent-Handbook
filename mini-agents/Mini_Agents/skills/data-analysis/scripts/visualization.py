"""
Data Visualization Script

Creates various data visualizations
"""

import numpy as np
import matplotlib.pyplot as plt


def create_sample_data():
    """Create sample data for visualization"""
    np.random.seed(42)
    
    # Generate different types of data
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x)
    y2 = np.cos(x)
    y3 = np.random.randn(100)
    
    return x, y1, y2, y3


def plot_line_chart(x, y1, y2):
    """Create a line chart"""
    plt.figure(figsize=(10, 6))
    plt.plot(x, y1, label='sin(x)', linewidth=2)
    plt.plot(x, y2, label='cos(x)', linewidth=2)
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Sine and Cosine Waves')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('line_chart.png', dpi=150, bbox_inches='tight')
    print("✅ Line chart saved to line_chart.png")
    plt.close()


def plot_histogram(data):
    """Create a histogram"""
    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=30, alpha=0.7, edgecolor='black')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('Histogram of Random Data')
    plt.grid(True, alpha=0.3, axis='y')
    plt.savefig('histogram.png', dpi=150, bbox_inches='tight')
    print("✅ Histogram saved to histogram.png")
    plt.close()


def plot_scatter(x, y):
    """Create a scatter plot"""
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, alpha=0.6, s=50)
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Scatter Plot')
    plt.grid(True, alpha=0.3)
    plt.savefig('scatter_plot.png', dpi=150, bbox_inches='tight')
    print("✅ Scatter plot saved to scatter_plot.png")
    plt.close()


def main():
    """Main function"""
    print("=== Data Visualization Script ===")
    
    # Create sample data
    x, y1, y2, y3 = create_sample_data()
    
    # Create various visualizations
    plot_line_chart(x, y1, y2)
    plot_histogram(y3)
    plot_scatter(x, y1)
    
    print("\n✅ All visualizations created successfully!")


if __name__ == "__main__":
    main()
