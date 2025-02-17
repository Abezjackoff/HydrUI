from .block import HydraulicQuantity
from scipy.optimize import fsolve

class HydraulicAssembly:
    def __init__(self):
        self.blocks = dict()
        self.states = []
        self.statesMerged = []
        self.statesConst = []

    def add_block(self, block, uid):
        if uid in self.blocks:
            raise Exception("Cannot add a new block. Block with the specified UID already exists.")
        self.blocks[uid] = block
        block.name = uid
        i = len(self.states)
        for state in block.states:
            state.set_blockId(uid)
            if state not in block.statesConst:
                state.set_assyId(i)
                self.states.append(state)
                i += 1
            else:
                state.set_assyId(None)
                self.statesConst.append(state)

    def set_stateVal(self, uid, port, qnty, value):
        globalId = self.get_stateId(uid, port, qnty)
        self.states[globalId].value = value
        self.update_mergedStVal()

    def get_localId(self, uid, port, qnty):
        if qnty == HydraulicQuantity.Q:
            localId = self.blocks[uid].ports[port].qId
        elif qnty == HydraulicQuantity.P:
            localId = self.blocks[uid].ports[port].pId
        else:
            raise Exception("Unknown state quantity. It shall be either Q or P.")
        return localId

    def get_stateId(self, uid, port, qnty):
        localId = self.get_localId(uid, port, qnty)
        globalId = self.blocks[uid].states[localId].get_assyId()
        if globalId is None:
            return None
        if globalId < 0 or globalId >= len(self.states):
            raise Exception("Unknown state. It might be nonexistent in the assembly.")
        return globalId

    def connect_blocks(self, uid1, uid2, port1=1, port2=0):
        if uid1 not in self.blocks or uid2 not in self.blocks:
            raise Exception("Cannot connect blocks. Both has to be added to the assembly first.")
        if port1 >= len(self.blocks[uid1].ports) or port2 >= len(self.blocks[uid2].ports):
            raise Exception("Cannot connect blocks. Required ports are missing.")
        if self.blocks[uid1].ports[port1].connected or self.blocks[uid2].ports[port2].connected:
            raise Exception("Cannot connect blocks. One of the ports is already connected.")

        QorP = HydraulicQuantity.Q
        qSrcId = self.get_stateId(uid1, port1, QorP)
        qDstId = self.get_stateId(uid2, port2, QorP)
        if qSrcId is not None and qDstId is not None:
            self.merge_states(qSrcId, qDstId)
        elif qSrcId is not None:
            self.make_constSt(uid1, port1, QorP, self.get_constVal(uid2, port2, QorP))
        elif qDstId is not None:
            self.make_constSt(uid2, port2, QorP, self.get_constVal(uid1, port1, QorP))

        QorP = HydraulicQuantity.P
        pSrcId = self.get_stateId(uid1, port1, QorP)
        pDstId = self.get_stateId(uid2, port2, QorP)
        if pSrcId is not None and pDstId is not None:
            self.merge_states(pSrcId, pDstId)
        elif pSrcId is not None:
            self.make_constSt(uid1, port1, QorP, self.get_constVal(uid2, port2, QorP))
        elif pDstId is not None:
            self.make_constSt(uid2, port2, QorP, self.get_constVal(uid1, port1, QorP))

        self.blocks[uid1].ports[port1].connected = True
        self.blocks[uid2].ports[port2].connected = True

    def merge_states(self, srcId, dstId):
        if srcId >= len(self.states) or dstId >= len(self.states):
            raise Exception("Cannot merge states. Required state doesn't exist.")

        if srcId == dstId:
            return
        elif srcId > dstId:
            srcId -= 1

        dstState = self.pop_state(dstId)
        dstState.set_assyId(srcId)

        self.reindex_merged(srcId, dstId)
        self.statesMerged.append(dstState)

    def pop_state(self, index):
        state = self.states.pop(index)
        for i in range(index, len(self.states)):
            self.states[i].set_assyId(i)
        return state

    def reindex_merged(self, srcId, dstId):
        for state in self.statesMerged:
            i = state.get_assyId()
            if i == dstId:
                state.set_assyId(srcId)
            elif i > dstId:
                state.set_assyId(i - 1)

    def update_mergedStVal(self):
        for state in self.statesMerged:
            i = state.get_assyId()
            state.value = self.states[i].value

    def make_constSt(self, uid, port, qnty, value):
        constId = self.get_stateId(uid, port, qnty)
        constState = self.pop_state(constId)
        constState.set_assyId(None)
        constState.value = value

        self.reindex_merged(None, constId)
        self.statesConst.append(constState)

        for state in self.statesMerged:
            i = state.get_assyId()
            if i is None:
                state.value = value
                self.statesConst.append(state)
        self.statesMerged = [state for state in self.statesMerged if state.get_assyId() is not None]

    def get_constVal(self, uid, port, qnty):
        localId = self.get_localId(uid, port, qnty)
        return self.blocks[uid].states[localId].value

    def get_avg_pressure(self):
        p = 0
        if not self.statesConst:
            return p
        for state in self.statesConst:
            if state.qnty == HydraulicQuantity.P:
                p += state.value
        p /= len(self.statesConst)
        return p

    def set_init_pressure(self, p0):
        for state in self.states:
            if state.qnty == HydraulicQuantity.P:
                state.value = p0
        self.update_mergedStVal()

    def get_init_values(self):
        x0 = []
        for state in self.states:
            x0.append(state.value)
        return x0

    def set_states_val(self, x):
        for i in range(len(self.states)):
            self.states[i].value = x[i]
        self.update_mergedStVal()

    def qp_balance(self, x):
        self.set_states_val(x)
        y = []
        for block in self.blocks.values():
            balance = block.qp_balance()
            if balance is not None:
                y.append(block.qp_balance())
        return y

    def solve(self):
        # TODO: check connections
        x0 = self.get_init_values()
        y = self.qp_balance(x0)
        if (len(x0) > len(y)):
            raise Exception("Not enough balance equations to solve for all unknown Q and P.")
        elif (len(x0) < len(y)):
            for i in range(len(y) - len(x0)):
                x0.append(0.)
        x, info, ier, msg = fsolve(self.qp_balance, x0, full_output=True)
        self.set_states_val(x)
        return x, ier == 1

    def states_to_dict(self):
        keys = []
        vals = []
        for state in self.states:
            keys.append(f'{state.get_blockId()}.{state.name}')
            vals.append(state.value)
        return dict(zip(keys, vals))
