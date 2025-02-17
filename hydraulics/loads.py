from .block import HydraulicQuantity, BlockState, BlockPort, HydraulicBlock
import numpy as np

class HydraulicResistance(HydraulicBlock):
    def __init__(self, q, p):
        if len(q) < 2 or len(p) < 2:
            raise Exception("P-Q table shall have at least 2 reference points.")
        if len(q) != len(p):
            raise Exception("P-Q table data and breakpoints shall have equal length.")
        super().__init__(1, 1)
        self.states = [BlockState(HydraulicQuantity.Q, 'q'),
                       BlockState(HydraulicQuantity.P, 'p_in'),
                       BlockState(HydraulicQuantity.P, 'p_out')]
        self.ports = [BlockPort('inlet', 0, 1),
                      BlockPort('outlet', 0, 2)]
        self.qData = np.array(q)
        self.pData = np.array(p)

    def qp_lut(self, q):
        s = int(q > 0) - int(q < 0)
        q = abs(q)
        if q <= self.qData[-1]:
            return s * np.interp(q, self.qData, self.pData)
        else:
            return s * (self.pData[-2] + (q - self.qData[-2]) * (self.pData[-1] - self.pData[-2]) /
                                                                (self.qData[-1] - self.qData[-2]))

    def qp_balance(self):
        q = self.states[0].value
        p_in = self.states[1].value
        p_out = self.states[2].value
        return self.qp_balance_aux(q, p_in, p_out)

    def qp_balance_aux(self, q, p_in, p_out):
        return p_in - p_out - self.qp_lut(q)
