import asyncio
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
# 添加PocketFlow目录到Python路径，确保使用项目中的版本
pocketflow_path = os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow')
if pocketflow_path not in sys.path:
    sys.path.insert(0, pocketflow_path)

from utils.utils import call_llm_async

async def test_concurrent_calls():
    """测试并发调用"""
    print("=== 测试并发调用 ===")
    
    topic = "太空探索的历史"
    
    # 创建任务
    tasks = [
        call_llm_async(f"请总结关于'{topic}'的核心内容，控制在200字以内。"),
        call_llm_async(f"基于'{topic}'这个主题，生成5个有深度的问题。"),
        call_llm_async(f"从'{topic}'中提取并解释10个关键术语。")
    ]
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    concurrent_time = end_time - start_time
    
    print(f"并发调用时间: {concurrent_time:.2f} 秒")
    print(f"结果1 (总结): {results[0][:100]}...")
    print(f"结果2 (问题): {results[1][:100]}...")
    print(f"结果3 (术语): {results[2][:100]}...")
    
    return concurrent_time

async def test_sequential_calls():
    """测试顺序调用"""
    print("\n=== 测试顺序调用 ===")
    
    topic = "太空探索的历史"
    
    start_time = time.time()
    
    # 顺序执行
    result1 = await call_llm_async(f"请总结关于'{topic}'的核心内容，控制在200字以内。")
    result2 = await call_llm_async(f"基于'{topic}'这个主题，生成5个有深度的问题。")
    result3 = await call_llm_async(f"从'{topic}'中提取并解释10个关键术语。")
    
    end_time = time.time()
    
    sequential_time = end_time - start_time
    
    print(f"顺序调用时间: {sequential_time:.2f} 秒")
    print(f"结果1 (总结): {result1[:100]}...")
    print(f"结果2 (问题): {result2[:100]}...")
    print(f"结果3 (术语): {result3[:100]}...")
    
    return sequential_time

async def main():
    """主函数"""
    print("开始测试并发与顺序调用的时间差异...\n")
    
    # 运行测试
    concurrent_time = await test_concurrent_calls()
    sequential_time = await test_sequential_calls()
    
    # 计算性能指标
    speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0
    efficiency = (speedup - 1) * 100
    
    print("\n=== 性能对比 ===")
    print(f"并发调用时间: {concurrent_time:.2f} 秒")
    print(f"顺序调用时间: {sequential_time:.2f} 秒")
    print(f"加速比: {speedup:.2f}x")
    print(f"效率提升: {efficiency:.1f}%")
    
    # 分析结果
    if speedup > 1:
        print("\n✅ 并发调用比顺序调用更快，并行处理有效!")
    else:
        print("\n❌ 并发调用比顺序调用更慢，可能原因:")
        print("   - API服务器对并发请求有限制")
        print("   - 网络延迟或服务器负载")
        print("   - 并发创建任务的开销大于收益")

if __name__ == "__main__":
    asyncio.run(main())