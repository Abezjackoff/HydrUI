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
        s = np.sign(q)
        q = np.abs(q)
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


class HydraulicValve(HydraulicBlock):
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
        self._openPct = 0

    def set_openPct(self, opening):
        self._openPct = opening

    def get_openPct(self):
        return self._openPct

    def pq_lut(self, p):
        s = np.sign(p)
        p = np.abs(p)
        openFrac = self._openPct / 100.
        if p <= self.pData[-1]:
            return s * openFrac * np.interp(p, self.pData, self.qData)
        else:
            return s * openFrac * (self.qData[-2] + (p - self.pData[-2]) * (self.qData[-1] - self.qData[-2]) /
                                                                           (self.pData[-1] - self.pData[-2]))

    def qp_balance(self):
        q = self.states[0].value
        p_in = self.states[1].value
        p_out = self.states[2].value
        return self.qp_balance_aux(q, p_in, p_out)

    def qp_balance_aux(self, q, p_in, p_out):
        return q - self.pq_lut(p_in - p_out)


class HydraulicPipe(HydraulicBlock):
    def __init__(self, d, l):
        if d <= 0:
            raise Exception("Inner diameter shall be positive.")
        if l < 0:
            raise Exception("Pipe length shall be non-negative.")
        super().__init__(1, 1)
        self.states = [BlockState(HydraulicQuantity.Q, 'q'),
                       BlockState(HydraulicQuantity.P, 'p_in'),
                       BlockState(HydraulicQuantity.P, 'p_out')]
        self.ports = [BlockPort('inlet', 0, 1),
                      BlockPort('outlet', 0, 2)]
        self.d = d
        self.l = l
        self.rho = 1000
        self.eta = 0.9e-3

    def qp_balance(self):
        q = self.states[0].value
        p_in = self.states[1].value
        p_out = self.states[2].value
        v = np.abs(q) * 1e-3 / 60. / (0.25 * np.pi * self.d ** 2)
        Re = v * self.d * self.rho / self.eta
        if Re < 2300:
            lm = 64. / max(Re, 1e-6)
        else:
            lm = 0.3164 / np.power(max(Re, 1e-6), 0.25)
        k = 1e-3 * lm * self.rho * self.l / self.d
        return p_in - p_out - np.sign(q) * 0.5 * k * v ** 2
