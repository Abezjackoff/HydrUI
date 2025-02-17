from enum import Enum
import abc

class HydraulicQuantity(str, Enum):
    P = 'P'
    Q = 'Q'

class BlockState:
    def __init__(self, qnty: HydraulicQuantity, name: str, value=0):
        self.qnty = qnty
        self.name = name
        self.value = value
        self._blockId = None
        self._assyId = None

    def set_blockId(self, id):
        self._blockId = id

    def get_blockId(self):
        return self._blockId

    def set_assyId(self, id):
        self._assyId = id

    def get_assyId(self):
        return self._assyId

class BlockPort:
    def __init__(self, name: str, qId, pId):
        self.name = name
        self.qId = qId
        self.pId = pId
        self.connected = False

class HydraulicBlock:
    def __init__(self, n_in, n_out):
        self.name = None
        self.states = []
        self.statesConst = []
        self.ports = []
        self.n_in = n_in
        self.n_out = n_out

    @abc.abstractmethod
    def qp_balance(self, *args):
        pass
