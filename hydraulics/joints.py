from .block import HydraulicQuantity, BlockState, BlockPort, HydraulicBlock

class HeaderTank(HydraulicBlock):
    def __init__(self, pressure):
        super().__init__(1, 1)
        self.states = [BlockState(HydraulicQuantity.Q, 'q'),
                       BlockState(HydraulicQuantity.P, 'p')]
        self.statesConst = [self.states[1]]
        self.ports = [BlockPort('inlet', 0, 1),
                      BlockPort('outlet', 0, 1)]
        self._set_pConst(pressure)

    def _set_pConst(self, pressure):
        self.states[1].value = pressure

    def qp_balance(self):
        return None

class TeeSplit(HydraulicBlock):
    def __init__(self):
        super().__init__(1, 2)
        self.states = [BlockState(HydraulicQuantity.Q, 'q_in'),
                       BlockState(HydraulicQuantity.Q, 'q_out1'),
                       BlockState(HydraulicQuantity.Q, 'q_out2'),
                       BlockState(HydraulicQuantity.P, 'p')]
        self.ports = [BlockPort('inlet', 0, 3),
                      BlockPort('outlet1', 1, 3),
                      BlockPort('outlet2', 2, 3)]

    def qp_balance(self):
        q_in = self.states[0].value
        q_out1 = self.states[1].value
        q_out2 = self.states[2].value
        return q_in - q_out1 - q_out2


class TeeJoin(HydraulicBlock):
    def __init__(self):
        super().__init__(2, 1)
        self.states = [BlockState(HydraulicQuantity.Q, 'q_in1'),
                       BlockState(HydraulicQuantity.Q, 'q_in2'),
                       BlockState(HydraulicQuantity.Q, 'q_out'),
                       BlockState(HydraulicQuantity.P, 'p')]
        self.ports = [BlockPort('inlet1', 0, 3),
                      BlockPort('inlet2', 1, 3),
                      BlockPort('outlet', 2, 3)]

    def qp_balance(self):
        q_in1 = self.states[0].value
        q_in2 = self.states[1].value
        q_out = self.states[2].value
        return q_in1 + q_in2 - q_out

class MultiPortJoint(HydraulicBlock):
    def __init__(self, n_in=1, n_out=1):
        super().__init__(n_in, n_out)
        self.states = []
        self.ports = []
        for i in range(n_in):
            self.states.append(BlockState(HydraulicQuantity.Q, f'q_in{i + 1}'))
            self.ports.append(BlockPort(f'inlet{i + 1}', i, n_in + n_out))
        for i in range(n_out):
            self.states.append(BlockState(HydraulicQuantity.Q, f'q_out{i + 1}'))
            self.ports.append(BlockPort(f'outlet{i + 1}', n_in + i, n_in + n_out))
        self.states.append(BlockState(HydraulicQuantity.P, 'p'))

    def qp_balance(self):
        qDiff = 0.
        for i in range(self.n_in):
            qDiff += self.states[i].value
        for i in range(self.n_out):
            qDiff -= self.states[self.n_in + i].value
        return qDiff
