---
name: data-analysis
description: Skill for data analysis and visualization using Python
---

# Data Analysis Skill

This skill provides guidance and tools for data analysis and visualization tasks using Python.

## Overview

This skill includes Python code snippets and scripts for common data analysis tasks:
- Data loading and exploration
- Statistical analysis
- Data visualization
- Data cleaning and preprocessing

## Available Scripts

### 1. Basic Statistics

Use `execute_script` to run the statistics script:
```python
python /nfs/FM/gongoubo/new_project/Agent-Handbook/mini-agents/Mini_Agents/skills/data-analysis/scripts/basic_stats.py
```

### 2. Data Visualization

Use `execute_script` to run the visualization script:
```python
python /nfs/FM/gongoubo/new_project/Agent-Handbook/mini-agents/Mini_Agents/skills/data-analysis/scripts/visualization.py
```

### 3. Quick Code Execution

For quick analysis, use `execute_code` with inline Python code:

```python
import numpy as np
import pandas as pd

# Create sample data
data = np.random.randn(100)
print(f"Mean: {np.mean(data):.2f}")
print(f"Std: {np.std(data):.2f}")
print(f"Min: {np.min(data):.2f}")
print(f"Max: {np.max(data):.2f}")
```

## Usage Examples

### Example 1: Calculate Statistics

Use `execute_code` tool:
```python
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
mean = sum(data) / len(data)
print(f"Mean: {mean}")
```

### Example 2: Load and Analyze CSV

Use `execute_code` tool:
```python
import pandas as pd

# Load data from CSV
df = pd.read_csv('data.csv')

# Display basic info
print(df.info())
print(df.describe())

# Calculate correlations
print(df.corr())
```

### Example 3: Create Visualization

Use `execute_code` tool:
```python
import matplotlib.pyplot as plt
import numpy as np

# Create sample data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create plot
plt.figure(figsize=(10, 6))
plt.plot(x, y, label='sin(x)')
plt.xlabel('x')
plt.ylabel('y')
plt.title('Sine Wave')
plt.legend()
plt.grid(True)
plt.savefig('plot.png')
print("Plot saved to plot.png")
```

## Best Practices

1. Always check if required libraries are installed before executing code
2. Use `execute_code` for quick, one-off analyses
3. Use `execute_script` for complex, reusable scripts
4. Handle errors gracefully and provide meaningful error messages
5. Clean up temporary files after execution

## Required Libraries

- numpy
- pandas
- matplotlib
- scipy

Install with: `pip install numpy pandas matplotlib scipy`
