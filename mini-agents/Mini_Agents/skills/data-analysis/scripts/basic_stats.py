"""
Basic Statistics Script

Calculates basic statistics for numerical data
"""

import sys
import numpy as np


def calculate_statistics(data):
    """Calculate basic statistics for a list of numbers"""
    data = np.array(data)
    
    stats = {
        'count': len(data),
        'mean': np.mean(data),
        'median': np.median(data),
        'std': np.std(data),
        'var': np.var(data),
        'min': np.min(data),
        'max': np.max(data),
        'q25': np.percentile(data, 25),
        'q75': np.percentile(data, 75),
    }
    
    return stats


def main():
    """Main function"""
    # Example data - replace with your actual data
    if len(sys.argv) > 1:
        # Data provided as command line arguments
        data = [float(x) for x in sys.argv[1:]]
    else:
        # Use sample data
        data = np.random.randn(100) * 10 + 50
    
    # Calculate statistics
    stats = calculate_statistics(data)
    
    # Print results
    print("=== Basic Statistics ===")
    print(f"Count:    {stats['count']}")
    print(f"Mean:     {stats['mean']:.2f}")
    print(f"Median:   {stats['median']:.2f}")
    print(f"Std Dev:  {stats['std']:.2f}")
    print(f"Variance: {stats['var']:.2f}")
    print(f"Min:      {stats['min']:.2f}")
    print(f"Max:      {stats['max']:.2f}")
    print(f"Q25:      {stats['q25']:.2f}")
    print(f"Q75:      {stats['q75']:.2f}")
    print(f"Range:    {stats['max'] - stats['min']:.2f}")


if __name__ == "__main__":
    main()
