import asyncio, warnings, copy, time

class BaseNode:
    def __init__(self): self.params,self.successors={},{}
    def set_params(self,params): self.params=params
    def next(self,node,action="default"):
        if action in self.successors: warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action]=node; return node
    def prep(self,shared): pass
    def exec(self,prep_res): pass
    def post(self,shared,prep_res,exec_res): pass
    def _exec(self,prep_res): return self.exec(prep_res)
    def _run(self,shared): p=self.prep(shared); e=self._exec(p); return self.post(shared,p,e)
    def run(self,shared): 
        if self.successors: warnings.warn("Node won't run successors. Use Flow.")  
        return self._run(shared)
    def __rshift__(self,other): return self.next(other)
    def __sub__(self,action):
        if isinstance(action,str): return _ConditionalTransition(self,action)
        raise TypeError("Action must be a string")

class _ConditionalTransition:
    def __init__(self,src,action): self.src,self.action=src,action
    def __rshift__(self,tgt): return self.src.next(tgt,self.action)

class Node(BaseNode):
    def __init__(self,max_retries=1,wait=0): super().__init__(); self.max_retries,self.wait=max_retries,wait
    def exec_fallback(self,prep_res,exc): raise exc
    def _exec(self,prep_res):
        for self.cur_retry in range(self.max_retries):
            try: return self.exec(prep_res)
            except Exception as e:
                if self.cur_retry==self.max_retries-1: return self.exec_fallback(prep_res,e)
                if self.wait>0: time.sleep(self.wait)

class BatchNode(Node):
    def _exec(self,items): return [super(BatchNode,self)._exec(i) for i in (items or [])]

class Flow(BaseNode):
    def __init__(self,start=None): super().__init__(); self.start_node=start
    def start(self,start): self.start_node=start; return start
    def get_next_node(self,curr,action):
        nxt=curr.successors.get(action or "default")
        if not nxt and curr.successors: warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        return nxt
    def _orch(self,shared,params=None):
        curr,p,last_action =copy.copy(self.start_node),(params or {**self.params}),None
        while curr: curr.set_params(p); last_action=curr._run(shared); curr=copy.copy(self.get_next_node(curr,last_action))
        return last_action
    def _run(self,shared): p=self.prep(shared); o=self._orch(shared); return self.post(shared,p,o)
    def post(self,shared,prep_res,exec_res): return exec_res

class BatchFlow(Flow):
    def _run(self,shared):
        pr=self.prep(shared) or []
        for bp in pr: self._orch(shared,{**self.params,**bp})
        return self.post(shared,pr,None)

class AsyncNode(Node):
    async def prep_async(self,shared): pass
    async def exec_async(self,prep_res): pass
    async def exec_fallback_async(self,prep_res,exc): raise exc
    async def post_async(self,shared,prep_res,exec_res): pass
    async def _exec(self,prep_res): 
        print(f"[DEBUG] AsyncNode._exec: Starting with prep_res={prep_res}")
        for self.cur_retry in range(self.max_retries):
            try: 
                result = await self.exec_async(prep_res)
                print(f"[DEBUG] AsyncNode._exec: exec_async returned {type(result)}")
                return result
            except Exception as e:
                print(f"[DEBUG] AsyncNode._exec: Exception occurred: {e}")
                if self.cur_retry==self.max_retries-1: return await self.exec_fallback_async(prep_res,e)
                if self.wait>0: await asyncio.sleep(self.wait)
    async def run_async(self,shared): 
        print(f"[DEBUG] AsyncFlow.run_async: Starting with shared={shared}")
        if self.successors: warnings.warn("Node won't run successors. Use AsyncFlow.")  
        result = await self._run_async(shared)
        print(f"[DEBUG] AsyncFlow.run_async: _run_async completed, result={result}")
        return result
    async def _run_async(self,shared): 
        print(f"[DEBUG] AsyncNode._run_async: Starting")
        p=await self.prep_async(shared); 
        print(f"[DEBUG] AsyncNode._run_async: prep_async completed, result={p}")
        e=await self._exec(p); 
        print(f"[DEBUG] AsyncNode._run_async: _exec completed, result={e}")
        print(f"[DEBUG] AsyncNode._run_async: About to call post_async with shared={type(shared)}, prep_res={type(p)}, exec_res={type(e)}")
        if isinstance(e, dict):
            print(f"[DEBUG] AsyncNode._run_async: exec_res keys={e.keys()}")
            if 'answer' in e:
                print(f"[DEBUG] AsyncNode._run_async: exec_res['answer'] length={len(e['answer'])}, content={e['answer'][:50]}")
        result=await self.post_async(shared,p,e)
        print(f"[DEBUG] AsyncNode._run_async: post_async completed, result={result}")
        return result
    def _run(self,shared): raise RuntimeError("Use run_async.")

class AsyncBatchNode(AsyncNode,BatchNode):
    async def _exec(self,items): return [await super(AsyncBatchNode,self)._exec(i) for i in items]

class AsyncParallelBatchNode(AsyncNode,BatchNode):
    async def _exec(self,items): return await asyncio.gather(*(super(AsyncParallelBatchNode,self)._exec(i) for i in items))

class AsyncFlow(Flow,AsyncNode):
    async def run_async(self,shared): 
        print(f"[DEBUG] AsyncFlow.run_async: Starting with shared={shared}")
        if self.successors: warnings.warn("Node won't run successors. Use AsyncFlow.")  
        result = await self._run_async(shared)
        print(f"[DEBUG] AsyncFlow.run_async: _run_async completed, result={result}")
        return result
    async def _orch_async(self,shared,params=None):
        print(f"[DEBUG] AsyncFlow._orch_async: Starting")
        curr,p,last_action =copy.copy(self.start_node),(params or {**self.params}),None
        node_result = None
        iteration = 0
        while curr: 
            iteration += 1
            print(f"[DEBUG] AsyncFlow._orch_async: Iteration {iteration}, curr={curr}")
            curr.set_params(p)
            if isinstance(curr,AsyncNode):
                print(f"[DEBUG] AsyncFlow._orch_async: Calling AsyncNode components separately")
                # 分别调用节点的各个组件，不包含post_async，由Flow统一处理
                prep_result = await curr.prep_async(shared)
                print(f"[DEBUG] AsyncFlow._orch_async: prep_async returned {type(prep_result)}")
                exec_result = await curr._exec(prep_result)
                print(f"[DEBUG] AsyncFlow._orch_async: _exec returned {type(exec_result)}")
                # 调用节点的post_async方法，让节点处理自己的结果
                node_result = await curr.post_async(shared, prep_result, exec_result)
                print(f"[DEBUG] AsyncFlow._orch_async: post_async returned {type(node_result)}")
                # 使用node_result作为last_action，因为post_async返回的是状态字符串
                last_action = node_result
            else:
                print(f"[DEBUG] AsyncFlow._orch_async: Calling Node._run")
                node_result = curr._run(shared)
                print(f"[DEBUG] AsyncFlow._orch_async: Node._run returned {type(node_result)}")
                last_action = node_result
            next_node = copy.copy(self.get_next_node(curr,last_action))
            print(f"[DEBUG] AsyncFlow._orch_async: Next node is {next_node}")
            curr = next_node
        print(f"[DEBUG] AsyncFlow._orch_async: Returning node_result={node_result}")
        return node_result
    async def _run_async(self,shared): 
        print(f"[DEBUG] AsyncFlow._run_async: Starting with shared={shared}", flush=True)
        p=await self.prep_async(shared); 
        print(f"[DEBUG] AsyncFlow._run_async: prep_async completed, result={p}", flush=True)
        o=await self._orch_async(shared); 
        print(f"[DEBUG] AsyncFlow._run_async: _orch_async completed, result={o}", flush=True)
        print(f"[DEBUG] AsyncFlow._run_async: _orch_async returned result type: {type(o)}", flush=True)
        print(f"[DEBUG] AsyncFlow._run_async: Final result before post_async: {o}", flush=True)
        
        # 对于Flow，_orch_async返回的是最后一个节点的post_async结果，通常是状态字符串
        # 我们不需要在这里处理字典结果，因为每个节点的post_async已经处理了
        result=await self.post_async(shared,p,o)
        print(f"[DEBUG] AsyncFlow._run_async: post_async completed, result={result}", flush=True)
        print(f"[DEBUG] AsyncFlow._run_async: _run_async returning result type: {type(result)}", flush=True)
        return result
    async def post_async(self,shared,prep_res,exec_res):
        print(f"DEBUG: AsyncFlow.post_async被调用", flush=True)
        print(f"DEBUG: exec_res类型: {type(exec_res)}", flush=True)
        
        # 对于Flow，exec_res是_orch_async的返回值，即最后一个节点的post_async结果
        # 我们不需要在这里处理字典结果，因为每个节点的post_async已经处理了
        # 直接返回exec_res，让调用者处理
        return exec_res

class AsyncBatchFlow(AsyncFlow,BatchFlow):
    async def _run_async(self,shared):
        pr=await self.prep_async(shared) or []
        for bp in pr: await self._orch_async(shared,{**self.params,**bp})
        return await self.post_async(shared,pr,None)

class AsyncParallelBatchFlow(AsyncFlow,BatchFlow):
    async def _run_async(self,shared): 
        pr=await self.prep_async(shared) or []
        await asyncio.gather(*(self._orch_async(shared,{**self.params,**bp}) for bp in pr))
        return await self.post_async(shared,pr,None)