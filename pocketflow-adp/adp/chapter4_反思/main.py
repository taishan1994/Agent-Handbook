import asyncio
import sys
import os
from flow import run_reflection_example

# 添加PocketFlow路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow'))

async def main():
    """主函数，演示反思模式的使用"""
    print("="*50)
    print("PocketFlow 反思模式演示")
    print("="*50)
    print("\n本演示将展示如何使用PocketFlow实现反思模式，")
    print("通过生成、评审和优化的迭代过程来改进Python函数。")
    print("\n任务：创建一个计算阶乘的Python函数")
    print("要求：包含文档字符串、处理边缘情况和错误输入")
    print("\n开始反思流程...\n")
    
    # 运行反思示例
    result = await run_reflection_example()
    
    # 打印总结
    print("\n" + "="*50)
    print("反思模式演示完成")
    print("="*50)
    print(f"\n总结:")
    print(f"- 总迭代次数: {result['total_iterations']}")
    print(f"- 是否成功完成: {'是' if result['completed_successfully'] else '否'}")
    
    if result['completed_successfully']:
        print("\n✅ 反思模式成功生成了满足所有要求的代码！")
    else:
        print("\n⚠️ 反思模式达到了最大迭代次数，但代码可能仍有改进空间。")
    
    print("\n反思模式的优势:")
    print("- 通过迭代改进提升代码质量")
    print("- 自动识别和修复问题")
    print("- 生成更完整和健壮的解决方案")
    
    print("\n与LangChain实现的对比:")
    print("- PocketFlow提供了更简洁的异步处理")
    print("- 节点定义更直观，流程控制更灵活")
    print("- 条件转换使迭代逻辑更清晰")


if __name__ == "__main__":
    asyncio.run(main())